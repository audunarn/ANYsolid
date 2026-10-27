"""Effective runtime and coverage receipt for the opt-in development runner."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys


def pytest_sessionfinish(session, exitstatus):
    from threadpoolctl import threadpool_info
    root = Path(__file__).resolve().parents[1]
    expected = {"anysolid": root / "src/anysolid",
                "anysolver": Path(os.environ["ANYSOLID_DEV_SOLVER"]) / "src/anysolver"}
    imports = {name: str(Path(module.__file__).resolve()) for name, module in dict(sys.modules).items()
               if name.split(".")[0] in expected and getattr(module, "__file__", None)}
    errors = ["wrong source import: " + name for name, path in imports.items()
              if not Path(path).is_relative_to(expected[name.split(".")[0]])]
    pools = threadpool_info()
    if any(p["num_threads"] != 1 for p in pools):
        errors.append("numerical thread pools are not single-threaded")
    numba = sys.modules.get("numba")
    if numba is not None and (numba.get_num_threads() != 1 or
            bool(numba.config.DISABLE_JIT) != (os.environ["NUMBA_DISABLE_JIT"] == "1")):
        errors.append("effective Numba settings differ from requested settings")
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    counts = {key: len(value) for key, value in reporter.stats.items()
              if key in ("passed", "failed", "skipped", "error", "xfailed", "xpassed", "deselected")}
    if not session.config.option.collectonly and not counts.get("passed"):
        errors.append("no passing tests executed")
    if errors and int(exitstatus) == 0:
        session.exitstatus = 1
    versions = {}
    for name in ("numpy", "scipy", "scikit-fem", "pytest", "numba", "threadpoolctl"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    record = {"imports": imports, "pools": pools, "versions": versions,
              "jit_disabled": bool(numba.config.DISABLE_JIT) if numba else None,
              "counts": counts, "collected": session.testscollected,
              "errors": errors, "exit_code": int(session.exitstatus)}
    Path(os.environ["ANYSOLID_DEV_RECORD"]).write_text(json.dumps(record, indent=2), encoding="utf-8")
