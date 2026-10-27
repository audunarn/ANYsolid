"""Development selection/refusal contracts; no numerical qualification runs."""
import json
from pathlib import Path

import pytest
from tools import dev_checks


def test_adapter_platform_runtime_probe_does_not_collide_with_venv(monkeypatch, tmp_path):
    """Exercise all phase orchestration with synthetic receipts, no FE/runtime."""
    from tools import adapter_platform_matrix as matrix
    tmp_path=tmp_path/('adapter-platform-synthetic-'+matrix.sha(Path(__file__))[:12]);tmp_path.mkdir()
    source=tmp_path/'source';source.mkdir()
    for name in ('src','tests','tools','examples'):(source/name).mkdir()
    for name in ('pyproject.toml','README.md','LICENSE','.github/workflows/ci.yml'):
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
    (tmp_path/'manifest.json').write_text('{}')
    manifest={'source_sha256':matrix.source_inventory(source)}
    output=tmp_path/'cells/windows311';(output/'runtime').mkdir(parents=True)
    matrix.save(output/'setup.json',{'python':'synthetic-python','manifest_sha256':matrix.sha(tmp_path/'manifest.json')})
    monkeypatch.setattr(matrix,'verify_source',lambda folder:manifest)
    def fake(command,folder,timeout,env,cwd):
        assert folder!=output/'runtime'
        folder.mkdir()
        record={'status':'completed','process_wall_seconds':.01,'cleanup':{'verified':True}}
        matrix.save(folder/'result.json',record)
        if 'pytest' in command:(output/'pytest.xml').write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>')
        if 'build' in command:
            dist=output/'dist';dist.mkdir();(dist/'fixture.whl').write_bytes(b'wheel');(dist/'fixture.tar.gz').write_bytes(b'sdist')
        return record
    monkeypatch.setattr(matrix,'run_process',fake)
    assert matrix.execute_cell(tmp_path,'windows311')==0
    assert (output/'runtime-probe/result.json').exists()
    assert not (output/'runtime/result.json').exists()


def test_adapter_linux_temporary_workspace_is_native_and_owned(tmp_path):
    from tools import adapter_platform_matrix as matrix
    stage=tmp_path/'adapter-platform-unique-fixture'
    cell=stage/'cells/linux311'
    assert str(matrix.temporary_root(cell,linux=True)).replace('\\','/')=='/tmp/anysolid-adapter-platform-unique-fixture/linux311'
    assert matrix.temporary_root(cell,linux=False)==cell/'tmp'
    import pytest
    # A pytest workspace may itself descend from an owned matrix stage.
    # Use a neutral absolute path to test genuinely missing stage ownership.
    with pytest.raises(ValueError):matrix.temporary_root(Path('/neutral-parent/not-a-stage'),linux=True)


def test_adapter_managed_interpreter_aliases_use_physical_identity(tmp_path):
    from tools import adapter_platform_matrix as matrix
    # Direct indirection avoids requiring Windows symlink privileges while
    # exercising the actual resolution/deduplication and ambiguity paths.
    class Alias:
        def __init__(self,target):self.target=target
        def resolve(self):return self.target
    physical=tmp_path/'physical-python'
    assert matrix.resolve_managed_interpreter([Alias(physical),Alias(physical)])==str(physical)
    with pytest.raises(ValueError):matrix.resolve_managed_interpreter([])
    with pytest.raises(ValueError):matrix.resolve_managed_interpreter([Alias(physical),Alias(tmp_path/'different-python')])


@pytest.mark.parametrize("profile", dev_checks.PROFILES)
def test_profiles_are_explicit_and_nonempty(profile, monkeypatch, tmp_path):
    # Checkout ancestors are not selected test targets. Exercise deployment
    # under an evidence/comparison-named parent without weakening target scope.
    monkeypatch.setattr(dev_checks,'ROOT',tmp_path/'evidence comparison parent'/'checkout')
    selected = dev_checks.selection(profile, Path("host"))
    assert selected and len(selected) == len(set(selected))
    targets=[Path(path.partition('::')[0]) for path in selected]
    relative=[path.relative_to(dev_checks.ROOT) if path.is_relative_to(dev_checks.ROOT) else path for path in targets]
    assert not any(part=='evidence' or 'comparison' in part for path in relative for part in path.parts)


def test_full_covers_all_current_adapter_modules():
    selected = dev_checks.selection("full", dev_checks.ROOT.parent / "ANYsolver")
    assert selected[0] == str(dev_checks.ROOT / "tests")
    assert {Path(path).name for path in selected[1:]} == {
        "test_solid_models.py", "test_solid_residuals.py", "test_solid_coupling.py",
        "test_solid_trace_extensions.py", "test_solid_multiplier_consistency.py",
        "test_solid_strong_diagnostic.py", "test_solid_interface_overlap.py",
        "test_e4_pl_functional_constructor_policy.py"}


@pytest.mark.parametrize("args", [["unknown"], ["backend", "--timeout", "0"],
                                ["host", "--solver-root", "missing-checkout"]])
def test_invalid_or_missing_selection_refused(args):
    with pytest.raises(SystemExit) as exc:
        dev_checks.main(args)
    assert exc.value.code == 2


def test_dry_run_does_not_launch(monkeypatch, capsys):
    def refuse(*args, **kwargs):
        raise AssertionError("dry run launched a process")
    monkeypatch.setattr(dev_checks.subprocess, "Popen", refuse)
    assert dev_checks.main(["smoke", "--dry-run"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert record["profile"] == "smoke"
    assert "tools.dev_runtime" in record["command"]


def test_backend_does_not_require_host_checkout(capsys):
    assert dev_checks.main(["backend", "--solver-root", "missing-checkout", "--dry-run"]) == 0
    record = json.loads(capsys.readouterr().out)
    assert str(dev_checks.ROOT / "tests") in record["command"]


@pytest.mark.parametrize("failure,expected", [(7, "failed"),
    (dev_checks.subprocess.TimeoutExpired("pytest", 1), "timeout"),
    (KeyboardInterrupt(), "interrupted"), (0, "invalid_runtime_receipt")])
def test_non_success_retains_attempt(monkeypatch, tmp_path, failure, expected):
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(dev_checks, "ROOT", tmp_path)
    terminated = []
    class Process:
        def wait(self, **kwargs):
            if isinstance(failure, BaseException):
                raise failure
            return failure
    monkeypatch.setattr(dev_checks.subprocess, "Popen", lambda *a, **k: Process())
    monkeypatch.setattr(dev_checks, "terminate", lambda process: terminated.append(process))
    assert dev_checks.main(["backend"]) != 0
    attempt, = (tmp_path / "evidence/development").iterdir()
    receipt = json.loads((attempt / "result.json").read_text())
    assert receipt["status"] == expected
    assert (attempt / "selection.json").is_file()
    assert (attempt / "stdout.log").is_file() and (attempt / "stderr.log").is_file()
    assert bool(terminated) == isinstance(failure, BaseException)
