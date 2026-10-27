"""Prospective W1.5 measurement; reuse equivalence is not physical qualification."""
from __future__ import annotations
import ctypes
import hashlib
import json
import os
from pathlib import Path
import sys
from time import perf_counter
import numpy as np
from scipy.sparse.linalg import splu
from skfem import MeshTet
from anysolid import SolidMesh, prepare
from anysolver.solids import SolidModel, ResidualScales

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/repeated_load_manifest.json"


def emit(row):
    print(json.dumps(row, allow_nan=False), flush=True)


def memory():
    if os.name == "nt":
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
                "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        api = ctypes.WinDLL("psapi", use_last_error=True).GetProcessMemoryInfo
        api.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if not api(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {"working_set_bytes": int(counters.WorkingSetSize),
                "lifetime_peak_working_set_bytes": int(counters.PeakWorkingSetSize)}
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"lifetime_peak_working_set_bytes": int(peak * (1 if sys.platform == "darwin" else 1024)),
            "working_set_bytes": None}


def relative(actual, expected):
    return float(np.max(np.abs(actual - expected), initial=0.) /
                 max(np.max(np.abs(expected), initial=0.), np.finfo(float).tiny))


def main():
    manifest = json.loads(MANIFEST.read_text())
    counts = manifest["counts"]
    if (any(not isinstance(n,int) or n <= 0 for n in counts) or
        sum(counts) > manifest["bounds"]["maximum_total_rhs"] or
        3 > manifest["bounds"]["maximum_reference_rhs"]):
        raise ValueError("prospective RHS budget invalid before any solve")
    emit({"type":"identity", "manifest":manifest,
          "manifest_sha256":hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
          "harness_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "memory_start":memory()})
    intervals, divisions = manifest["geometry"]["intervals_m"], manifest["geometry"]["subdivisions"]
    t0 = perf_counter()
    raw = MeshTet.init_tensor(*(np.linspace(a, b, n+1) for (a,b),n in zip(intervals,divisions))).oriented()
    initial = SolidMesh(raw.p.T, raw.t.T)
    facet_x = initial.coordinates[initial.boundary_facets,0]
    groups = {"clamp":initial.boundary_ids[np.all(facet_x == 0., axis=1)]}
    mesh = SolidMesh(initial.coordinates, initial.cells, boundary_groups=groups)
    conversion = perf_counter()-t0
    t0 = perf_counter()
    prepared = prepare(mesh, manifest["material"], order=2)
    preparation = perf_counter()-t0
    if prepared.ndof > manifest["bounds"]["maximum_solid_dofs"]:
        raise ValueError("prospective DOF bound exceeded")
    signature = prepared.cache_signature()
    t0 = perf_counter(); K = prepared.assemble_linear(); assembly = perf_counter()-t0
    t0 = perf_counter(); warm = prepared.assemble_linear(); assembly_copy = perf_counter()-t0
    if (K != warm).nnz:
        raise ValueError("warm operator differs")
    t0 = perf_counter()
    basis_loads = np.column_stack([prepared.body_load(0.001*np.eye(3)[i]) for i in range(3)])
    load_assembly = perf_counter()-t0
    fixed = prepared.boundary_dofs("clamp")
    free = np.setdiff1d(np.arange(prepared.ndof),fixed)
    reference = np.zeros_like(basis_loads)
    reference[free] = splu(K[free][:,free].tocsc()).solve(basis_loads[free])
    tensor_references = [prepared.recover(reference[:,i]) for i in range(3)]
    model = SolidModel()
    region = model.add_region("solid",prepared=prepared)
    region.prescribe("clamp",0.)
    scales = manifest["normalization"]
    norms = ResidualScales(scales["L_m"],scales["force_N"],scales["displacement_m"])
    limits = manifest["acceptance"]
    force_map = np.eye(3)[prepared.coefficient_components].T
    moment_map = np.cross(prepared.coefficient_coordinates,
                          np.eye(3)[prepared.coefficient_components]).T
    resultant_map = np.vstack((force_map,moment_map/scales["L_m"]))
    emit({"type":"preparation", "ndof":int(prepared.ndof),"cells":len(mesh.cells),
          "signature":signature,"conversion_seconds":conversion,"preparation_seconds":preparation,
          "cold_assembly_seconds":assembly,"warm_operator_copy_seconds":assembly_copy,
          "load_assembly_seconds":load_assembly,"coupling_seconds":None,
          "reference_factorizations":1,"reference_rhs":3,
          "coupling_note":"not applicable: all-solid workload",
          "stiffness_array_bytes":K.data.nbytes+K.indices.nbytes+K.indptr.nbytes})
    cumulative_rhs, previous_solve_time = 0, 0.
    for batch,count in enumerate(manifest["counts"]):
        names = tuple(f"rhs-{i}" for i in range(count))
        index = np.arange(count)
        weights = np.vstack((np.ones(count),0.5*np.cos(index),0.25*np.sin(index+0.3)))
        loads = basis_loads @ weights
        for i,name in enumerate(names):
            region.set_load(name,loads[:,i])
        t0 = perf_counter()
        result = model.solve_static(names,residual_scales={name:norms for name in names})
        host_time = perf_counter()-t0
        cumulative_rhs += count
        if cumulative_rhs > manifest["bounds"]["maximum_total_rhs"]:
            raise ValueError("RHS budget exceeded")
        diag = result.diagnostics
        if diag["factorization_count"] != 1 or diag["solve_count"] != cumulative_rhs or bool(diag["cache_hit"]) != bool(batch):
            raise ValueError("factorization reuse counters do not match workload")
        expected_coefficients = reference @ weights
        coefficient_error = max(relative(result.coefficients[:,i],expected_coefficients[:,i]) for i in range(count))
        strain_error, stress_error, recovery_seconds = 0., 0., 0.
        for i in range(count):
            t0 = perf_counter(); recovery = prepared.recover(result.coefficients[:,i]); recovery_seconds += perf_counter()-t0
            exact_strain = sum(weights[j,i]*tensor_references[j].strain for j in range(3))
            exact_stress = sum(weights[j,i]*tensor_references[j].stress for j in range(3))
            strain_error = max(strain_error,relative(recovery.strain,exact_strain))
            stress_error = max(stress_error,relative(recovery.stress,exact_stress))
        energy = np.sum(result.coefficients*(K @ result.coefficients),axis=0)
        work = np.sum(result.coefficients*loads,axis=0)
        work_error = max(relative(energy[i:i+1],work[i:i+1]) for i in range(count))
        support_reactions = np.zeros_like(loads)
        support_reactions[fixed] = result.reactions[fixed]
        resultant = resultant_map @ (support_reactions + loads)
        force_error = float(np.max(abs(resultant[:3])) / scales["force_N"])
        moment_error = float(np.max(abs(resultant[3:])) / scales["force_N"])
        balance = max(force_error,moment_error)
        residual = diag["registered_residual_report"]
        checks = {"equivalence":max(coefficient_error,strain_error,stress_error)<=limits["coefficient_tensor_equivalence_relative"],
                  "work":work_error<=limits["work_relative"], "balance":balance<=limits["force_moment_scaled"],
                  "residuals":bool(residual["passed"]),"signature_unchanged":prepared.cache_signature()==signature}
        emit({"type":"batch","rhs":count,"all_rhs_recovered":count,
              "host_total_seconds":host_time,"factorization_seconds_cumulative":diag["factorization_time"],
              "solve_seconds_increment":diag["solve_time"]-previous_solve_time,
              "full_recovery_seconds":recovery_seconds,"cache_hit":bool(diag["cache_hit"]),
              "factorization_count":diag["factorization_count"],"solve_count_cumulative":diag["solve_count"],
              "coefficient_error":coefficient_error,"strain_error":strain_error,"stress_error":stress_error,
              "work_error":work_error,"force_moment_scaled_error":balance,
              "force_scaled_error":force_error,"moment_scaled_error":moment_error,
              "registered_equilibrium":residual["normalized_equilibrium"],
              "registered_constraint":residual["normalized_constraint_error"],"checks":checks,
              "coefficient_array_bytes":result.coefficients.nbytes,"memory":memory()})
        if not all(checks.values()):
            raise ValueError("registered acceptance failed; attempt stops")
        previous_solve_time = diag["solve_time"]
        del result
    emit({"type":"terminal","status":"measured_reuse_equivalence_passed", "rhs":cumulative_rhs,
          "condensation":"disabled", "limitations":"all-solid finite workload; no speedup ratio, coupled-performance or elasticity qualification"})


if __name__ == "__main__":
    main()
