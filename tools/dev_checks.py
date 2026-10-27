"""Explicit, bounded source-development profiles; never scientific qualification."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ["tests/test_backend.py::" + name for name in (
    "test_import_is_lazy_and_has_no_sibling_imports",
    "test_prepare_import_is_lazy_and_missing_backend_error_is_actionable",
    "test_mesh_refusal", "test_affine_patch_full_tensor_energy")]
HOST = ["test_solid_models.py", "test_solid_residuals.py"]
PROFILES = ("smoke", "backend", "host", "coupling", "full", "tooling")


def selection(profile, solver):
    backend = [str(ROOT / "tests")]
    host = [str(solver / "tests" / name) for name in HOST]
    coupling = [str(solver / "tests" / name) for name in
                ("test_solid_coupling.py", "test_solid_trace_extensions.py",
                 "test_solid_multiplier_consistency.py", "test_solid_strong_diagnostic.py",
                 "test_solid_interface_overlap.py")]
    constructor_policy = [str(solver / "tests/test_e4_pl_functional_constructor_policy.py")]
    return {"smoke": [str(ROOT / item) for item in SMOKE],
            "backend": backend, "host": host, "coupling": coupling,
            "full": [str(ROOT / "tests"), *host, *coupling, *constructor_policy],
            "tooling": [str(ROOT / "tests/test_dev_checks.py")]}[profile]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def terminate(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait(timeout=15)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILES)
    parser.add_argument("--solver-root", type=Path, default=ROOT.parent / "ANYsolver")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--jit", choices=("on", "off"), default="on")
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    solver = args.solver_root.resolve()
    targets = selection(args.profile, solver)
    missing = [t for t in targets if not Path(t.partition("::")[0]).exists()]
    if missing:
        parser.error("missing selected tests: " + ", ".join(missing))
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "-p", "tools.dev_runtime", "--durations=5", *targets]
    if args.collect_only:
        command.append("--collect-only")
    if args.dry_run:
        print(json.dumps({"profile": args.profile, "command": command}, indent=2))
        return 0
    folder = ROOT / "evidence/development" / (
        dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    command.append("--junitxml=" + str(folder / "pytest.xml"))
    env = dict(os.environ)
    # Controlled imports and plugins, one numerical thread, compiled semantics by default.
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=os.pathsep.join(
        map(str, (ROOT, ROOT / "src", solver / "src"))),
        OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
        NUMEXPR_NUM_THREADS="1", NUMBA_NUM_THREADS="1",
        NUMBA_DISABLE_JIT="1" if args.jit == "off" else "0",
        ANYSOLID_DEV_RECORD=str(folder / "runtime.json"),
        ANYSOLID_DEV_SOLVER=str(solver), ANYSOLID_DEV_COLLECT=str(args.collect_only))
    inputs = [*ROOT.joinpath("src").rglob("*.py"), *ROOT.joinpath("tests").rglob("*.py"),
              *ROOT.joinpath("tools").glob("dev_*.py"), ROOT / "pyproject.toml"]
    if args.profile in ("host", "coupling", "full"):
        inputs += [*solver.joinpath("src").rglob("*.py"), solver / "pyproject.toml",
                   solver / "tests/conftest.py"]
        inputs += [Path(t.partition("::")[0]) for t in targets if Path(t.partition("::")[0]).is_file()]
    record = {"scope": "source development, not qualification or release",
              "profile": args.profile, "command": command, "cwd": str(ROOT),
              "python": sys.version, "timeout_seconds": args.timeout,
              "environment": {k: env[k] for k in ("PYTHONPATH", "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
                  "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                  "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT")},
              "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "sha256": {str(p): digest(p) for p in sorted(set(inputs)) if p.is_file()}}
    (folder / "selection.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    started = time.perf_counter()
    status, code = "startup_error", 1
    try:
        with (folder / "stdout.log").open("wb") as out, (folder / "stderr.log").open("wb") as err:
            options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=out, stderr=err, **options)
            try:
                code = process.wait(timeout=args.timeout)
                status = "completed" if code == 0 else "failed"
                if code == 0:
                    # A green process alone is not evidence that the runtime plugin ran.
                    try:
                        runtime = json.loads((folder / "runtime.json").read_text(encoding="utf-8"))
                        valid = runtime["exit_code"] == 0 and not runtime["errors"]
                        valid = valid and (args.collect_only or runtime["counts"].get("passed", 0) > 0)
                    except (OSError, ValueError, KeyError):
                        valid = False
                    if not valid:
                        status, code = "invalid_runtime_receipt", 1
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                status = "timeout" if isinstance(exc, subprocess.TimeoutExpired) else "interrupted"
                terminate(process)
                code = 124 if status == "timeout" else 130
    finally:
        receipt = {"status": status, "exit_code": code,
                   "process_wall_seconds": time.perf_counter() - started, "evidence": str(folder)}
        (folder / "result.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(json.dumps(receipt))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
