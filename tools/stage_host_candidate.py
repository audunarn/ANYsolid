"""Isolate the authorized host overlay from unrelated dirty sibling work."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT.parent / "ANYsolver"
OVERLAY = (
    "pyproject.toml", "THIRD_PARTY_NOTICES.md", "dependency-licenses.json",
    "src/anysolver/__init__.py", "src/anysolver/assembly.py", "src/anysolver/dynamics.py",
    "src/anysolver/modal.py", "src/anysolver/nonlinear_static.py",
    "src/anysolver/solids.py", "src/anysolver/solid_residuals.py", "src/anysolver/solid_trace.py",
    "tests/test_solid_models.py", "tests/test_solid_residuals.py", "tests/test_solid_coupling.py",
    "tests/test_solid_trace_extensions.py", "tests/test_solid_multiplier_consistency.py",
    "tests/test_solid_strong_diagnostic.py", "docs/SOLID_ADAPTER.md", "docs/SOLID_TRACE_EXTENSIONS.md",
    "tests/test_solid_interface_overlap.py",
    "tests/test_e4_pl_functional_constructor_policy.py",
)


if __name__ == "__main__":
    folder = ROOT / "evidence/w1" / ("host-stage-" + uuid.uuid4().hex[:10])
    folder.mkdir(parents=True)
    revision = subprocess.check_output(["git","rev-parse","HEAD"],cwd=HOST,text=True,timeout=15).strip()
    archive = folder / "baseline.zip"
    # Do not archive unrelated historical reports/campaign outputs: this stages
    # package inputs and owner test support, not a claim of complete checkout CI.
    inputs = ["src","packages","pyproject.toml","setup.py","MANIFEST.in","README.md",
              "LICENSE","COPYRIGHT","THIRD_PARTY_NOTICES.md","dependency-licenses.json",
              "scripts/check_license_compliance.py","scripts/retirement_policy.py","tests/conftest.py"]
    manifest = subprocess.check_output(["git","show",revision+":MANIFEST.in"],cwd=HOST,text=True,timeout=15)
    inputs = list(dict.fromkeys([*inputs,*[line.removeprefix("include ").strip()
        for line in manifest.splitlines() if line.startswith("include ")]]))
    subprocess.run(["git","archive","--format=zip","--output="+str(archive),revision,*inputs],
                   cwd=HOST,check=True,timeout=30)
    source = folder / "source"
    source.mkdir()
    with zipfile.ZipFile(archive) as package:
        if any(not (source / member.filename).resolve().is_relative_to(source.resolve()) for member in package.infolist()):
            raise ValueError("archive path escapes staging directory")
        package.extractall(source)
    hashes = {}
    for name in OVERLAY:
        data = (HOST/name).read_bytes()
        destination = source/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    identity = {"scope":"isolated tracked baseline plus explicit owned overlay; not full clean-checkout CI",
                "source":str(source),"host_baseline":revision,"overlay_sha256":hashes,
                "baseline_archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
                "baseline_selected_inputs":inputs,
                "excluded_unrelated_dirty_paths":["src/anysolver_results/__init__.py",
                    "src/anysolver_results/principals.py","tests/test_results_principal_axes.py"]}
    (folder/"identity.json").write_text(json.dumps(identity,indent=2),encoding="utf-8")
    print(json.dumps({"source":str(source),"identity":str(folder/"identity.json")}))
