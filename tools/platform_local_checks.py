"""Stage and audit one Windows/Python portable inventory; execution is explicit.

This is tracked baseline plus an owned overlay, never a clean-checkout claim.
The run phase belongs inside tools/run_check.py's process-tree supervisor.
"""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT.parent / 'ANYsolver'
EXCLUDED_TOP = {'.qualification', '.development'}
PROTECTED = ('src/anysolver_results/__init__.py', 'src/anysolver_results/principals.py',
             'tests/test_results_principal_axes.py')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2), encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git', '-C', str(HOST), *args], text=True, timeout=30).strip()


def overlay_paths():
    source = ROOT / 'tools/stage_host_candidate.py'
    tree = ast.parse(source.read_text())
    return ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'OVERLAY' for t in n.targets)))


def protected_hashes():
    return {p: sha(HOST / p) if (HOST / p).is_file() else None for p in PROTECTED}


def stage_path(value):
    folder = Path(value).resolve()
    boundary = (ROOT / 'evidence/w1').resolve()
    if folder.parent != boundary or not folder.name.startswith('platform-local-'):
        raise ValueError('stage must be an owned platform-local evidence directory')
    return folder


def effective_environment(folder):
    env = dict(os.environ)
    env.pop('PYTEST_ADDOPTS', None)
    env.pop('PYTEST_PLUGINS', None)
    paths = [folder/'source/src', ROOT/'src'] + [ROOT.parent/n/'src' for n in
        ('ANYmaterial', 'ANYmesh', 'ANYgeometry', 'ANYfileIO')]
    env.update(PYTHONPATH=os.pathsep.join(map(str, paths)), OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1',
        NUMEXPR_NUM_THREADS='1', NUMBA_DISABLE_JIT='0', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', RUNNER_TEMP=str(folder/'portable-output'))
    return env


def runtime(folder):
    # This child is launched with the final environment, not run_check's inherited
    # working-checkout PYTHONPATH. No FE objects or test functions are evaluated.
    import anysolver, anysolid, numpy, scipy, scipy.linalg, numba, psutil, mpmath, win32job
    import anymaterial, anymesher, anygeometry, anyfileio
    from threadpoolctl import threadpool_info
    host_origin = Path(anysolver.__file__).resolve()
    if not host_origin.is_relative_to(folder/'source/src'):
        raise ValueError(f'host import escaped staged source: {host_origin}')
    if not Path(anysolid.__file__).resolve().is_relative_to(ROOT/'src'):
        raise ValueError('adapter import escaped source owner')
    sibling_origins={}
    for module,owner in ((anymaterial,'ANYmaterial'),(anymesher,'ANYmesh'),
                         (anygeometry,'ANYgeometry'),(anyfileio,'ANYfileIO')):
        origin=Path(module.__file__).resolve()
        if not origin.is_relative_to(ROOT.parent/owner/'src'):
            raise ValueError(f'sibling import escaped explicit source owner: {owner}')
        sibling_origins[owner]=str(origin)
    pools = threadpool_info()
    if not pools or any(p['num_threads'] != 1 for p in pools):
        raise ValueError('numerical pools are not effectively single threaded')
    if numba.config.DISABLE_JIT:
        raise ValueError('compiled path disabled')
    source = folder/'source'
    sys.path.insert(0, str(source))
    spec = importlib.util.spec_from_file_location('_platform_portable_inventory', source/'scripts/run_portable_ci.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    modules = module.merge_test_modules()
    input_paths = sorted(set([*source.joinpath('src').rglob('*.py'),
        *source.joinpath('scripts').rglob('*.py'), *source.joinpath('tests').rglob('*.py'),
        source/'pyproject.toml', source/'tests/conftest.py']))
    record = {'python':sys.version, 'executable':sys.executable, 'host_origin':str(host_origin),
        'adapter_origin':anysolid.__file__, 'sibling_owner_origins':sibling_origins,
        'versions':{'numpy':numpy.__version__,
        'scipy':scipy.__version__, 'numba':numba.__version__, 'psutil':psutil.__version__,
        'mpmath':mpmath.__version__, 'pywin32':importlib.metadata.version('pywin32'),
        'llvmlite':importlib.metadata.version('llvmlite')},
        'dependency_origins':{'numba':numba.__file__,'psutil':psutil.__file__,
                            'mpmath':mpmath.__file__,'win32job':win32job.__file__}, 'actual_pools':pools,
        'jit_disabled':bool(numba.config.DISABLE_JIT), 'environment':{k:os.environ.get(k) for k in
        ('PYTHONPATH','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS',
         'NUMBA_DISABLE_JIT','RUNNER_TEMP','PYTEST_DISABLE_PLUGIN_AUTOLOAD')},
        'canonical_module_count':len(modules), 'canonical_modules':list(modules),
        'stage_source_test_sha256':{str(p.relative_to(source)):sha(p) for p in input_paths if p.is_file()},
        'scope':'source overlay Windows/Python3.11 inventory, no installed/clean-checkout/cross-platform acceptance'}
    save(folder/'runtime.json', record)
    print(json.dumps({'runtime_audited':True,'modules':len(modules),'host_origin':str(host_origin)}))


def reaudit(folder, python):
    """Re-audit an existing immutable source stage with a root-provided runtime."""
    python=Path(python).resolve()
    if not python.is_relative_to(folder/'runtime-env') or not python.is_file():
        raise ValueError('root-provided isolated runtime must belong to this stage')
    identity=json.loads((folder/'identity.json').read_text())
    if identity['attempt_consumed'] is not False:
        raise ValueError('cannot reprepare a consumed portable attempt')
    if identity['protected_working_files_after']!=protected_hashes():
        raise ValueError('protected working-file identity changed')
    for name,digest in identity['overlay_sha256'].items():
        if sha(folder/'source'/name)!=digest:raise ValueError('owned staged overlay changed')
    previous=dict(identity)
    save(folder/('identity-before-reaudit-'+uuid.uuid4().hex[:8]+'.json'),previous)
    identity.update(runtime_python=str(python),tool_sha256=sha(__file__),
        canonical_command=[str(python),'scripts/run_portable_ci.py','--workers','2','--timeout-seconds','2400'],
        execution_authorized=False)
    save(folder/'identity.json',identity)
    token=uuid.uuid4().hex[:8];env=effective_environment(folder)
    start=time.perf_counter()
    command=[str(python),str(Path(__file__).resolve()),'runtime','--stage',str(folder)]
    with (folder/f'preflight-{token}.stdout.txt').open('wb') as out,(folder/f'preflight-{token}.stderr.txt').open('wb') as err:
        check=subprocess.run(command,cwd=folder/'source',env=env,stdout=out,stderr=err,timeout=60)
    save(folder/f'preflight-{token}.receipt.json',{'command':command,'cwd':str(folder/'source'),
        'exit_code':check.returncode,'timeout_seconds':60,'process_wall_seconds':time.perf_counter()-start})
    identity['preflight_exit_code']=check.returncode;save(folder/'identity.json',identity)
    print(json.dumps({'stage':str(folder),'preflight_exit_code':check.returncode,'runtime_python':str(python),
                     'portable_executed':False,'preflight_receipt':f'preflight-{token}.receipt.json'}))
    check.check_returncode()


def prepare():
    folder = ROOT/'evidence/w1'/('platform-local-'+uuid.uuid4().hex[:10]); folder.mkdir(parents=True)
    before = protected_hashes(); revision = git('rev-parse','HEAD')
    top = git('ls-tree','--name-only',revision).splitlines()
    selected = [p for p in top if p not in EXCLUDED_TOP]
    if not selected or '.git' in selected:
        raise ValueError('invalid tracked top-level inventory')
    usage = shutil.disk_usage(folder)
    if usage.free < 4*1024**3:
        raise ValueError('less than 4GiB free for bounded full staging')
    archive = folder/'baseline.zip'; command = ['git','-C',str(HOST),'archive','--format=zip',
        '--output='+str(archive),revision,*selected]
    start=time.perf_counter()
    with (folder/'archive.stdout.txt').open('wb') as out, (folder/'archive.stderr.txt').open('wb') as err:
        result=subprocess.run(command,stdout=out,stderr=err,timeout=180)
    save(folder/'archive-receipt.json',{'command':command,'timeout_seconds':180,
        'process_wall_seconds':time.perf_counter()-start,'exit_code':result.returncode})
    result.check_returncode()
    source=folder/'source'; source.mkdir()
    with zipfile.ZipFile(archive) as package:
        for info in package.infolist():
            target=(source/info.filename).resolve()
            if not target.is_relative_to(source.resolve()) or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('unsafe archive member')
        expanded=sum(i.file_size for i in package.infolist())
        package.extractall(source)
    overlays={}
    for name in overlay_paths():
        data=(HOST/name).read_bytes(); target=source/name; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data); overlays[name]=sha(target)
    identity={'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(), 'host_baseline':revision,
        'scope':'full tracked baseline except historical .qualification/.development plus explicit owned overlay; NOT full clean checkout',
        'baseline_top_level_inputs':selected,'excluded_top_levels':sorted(EXCLUDED_TOP),
        'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'expanded_archive_bytes':expanded,
        'overlay_authority_sha256':sha(ROOT/'tools/stage_host_candidate.py'),'overlay_sha256':overlays,
        'protected_working_files_before':before,'protected_working_files_after':protected_hashes(),
        'original_host_git_status':git('status','--short'),'tool_sha256':sha(__file__),
        'canonical_command':[sys.executable,'scripts/run_portable_ci.py','--workers','2','--timeout-seconds','2400'],
        'outer_timeout_seconds':2460,'execution_authorized':False,'attempt_consumed':False}
    save(folder/'identity.json',identity)
    if before!=protected_hashes(): raise ValueError('protected dirty files changed')
    env=effective_environment(folder)
    with (folder/'preflight.stdout.txt').open('wb') as out,(folder/'preflight.stderr.txt').open('wb') as err:
        check=subprocess.run([sys.executable,str(Path(__file__).resolve()),'runtime','--stage',str(folder)],
            cwd=source,env=env,stdout=out,stderr=err,timeout=60)
    identity['preflight_exit_code']=check.returncode; save(folder/'identity.json',identity)
    print(json.dumps({'stage':str(folder),'preflight_exit_code':check.returncode,'portable_executed':False}))
    check.check_returncode()


def run(folder):
    identity=json.loads((folder/'identity.json').read_text())
    if identity['execution_authorized'] is not True or identity['attempt_consumed'] is not False:
        raise ValueError('root review authorization missing or attempt already consumed')
    if Path(sys.executable).resolve()!=Path(identity['runtime_python']).resolve():
        raise ValueError('run must use the explicitly audited isolated interpreter')
    if identity['tool_sha256']!=sha(__file__) or identity['protected_working_files_after']!=protected_hashes():
        raise ValueError('tool or protected work identity changed')
    runtime_record=json.loads((folder/'runtime.json').read_text());source=folder/'source'
    for name,digest in runtime_record['stage_source_test_sha256'].items():
        if sha(source/name)!=digest: raise ValueError('staged source/test changed: '+name)
    identity['attempt_consumed']=True;save(folder/'identity.json',identity)
    command=identity['canonical_command'];env=effective_environment(folder)
    (folder/'portable-output').mkdir(exist_ok=True)
    save(folder/'execution-start.json',{'command':command,'cwd':str(source),
        'effective_environment':{k:env[k] for k in runtime_record['environment']},
        'outer_supervision':'must be launched through unchanged tools/run_check.py timeout2460'})
    start=time.perf_counter()
    # Parent run_check kill-on-close Job Object supervises this complete tree;
    # canonical runner itself enforces the shared 2400s timeout and no retries.
    with (folder/'portable.stdout.txt').open('wb') as out,(folder/'portable.stderr.txt').open('wb') as err:
        process=subprocess.run(command,cwd=source,env=env,stdout=out,stderr=err)
    save(folder/'execution-result.json',{'exit_code':process.returncode,'process_wall_seconds':time.perf_counter()-start,
        'protected_working_files_after':protected_hashes(),'full_portable_attempts':1})
    print(json.dumps({'stage':str(folder),'portable_exit_code':process.returncode}))
    return process.returncode


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('prepare','runtime','reaudit','run'));p.add_argument('--stage');p.add_argument('--python')
    args=p.parse_args()
    if args.phase=='prepare':prepare();return 0
    if not args.stage:p.error('--stage is required')
    folder=stage_path(args.stage)
    if args.phase=='runtime':runtime(folder);return 0
    if args.phase=='reaudit':
        if not args.python:p.error('--python is required for reaudit')
        reaudit(folder,args.python);return 0
    return run(folder)


if __name__=='__main__':raise SystemExit(main())
