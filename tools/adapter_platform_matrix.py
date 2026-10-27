"""Local eight-cell adapter CI snapshot; setup is separate from explicit run.

No host tests or scientific study is invoked. All runtimes/artifacts are owned
by a fresh evidence directory. Linux cleanup is verified on Linux itself.
"""
from __future__ import annotations
import argparse
import ctypes
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
VERSIONS=('311','312','313','314')
CELLS=tuple(platform+version for platform in ('windows','linux') for version in VERSIONS)
WINDOWS_PYTHONS={
    '311':'C:/Users/AudunArnesenNyhus/AppData/Local/Programs/Python/Python311/python.exe',
    '312':'C:/Users/AudunArnesenNyhus/AppData/Roaming/uv/python/cpython-3.12-windows-x86_64-none/python.exe',
    '313':'C:/Python/Python313/python.exe','314':'C:/Python/Python314/python.exe'}
WINDOWS_UV='C:/Python/Python314/Scripts/uv.exe'
LINUX_UV='/home/audunarn/.local/bin/uv'
LINUX_PYTHONS={'312':'/usr/bin/python3.12','313':'/home/audunarn/.local/bin/python3.13'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value): Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')


def emit(value): print(json.dumps(value),flush=True)


def source_inventory(root):
    files=[]
    for name in ('src','tests','tools','examples'):
        files.extend(p for p in (root/name).rglob('*') if p.is_file()
            and not any(part in ('__pycache__','build','dist','.pytest_cache') or part.endswith('.egg-info') for part in p.relative_to(root).parts)
            and p.suffix in ('.py','.json','.txt'))
    files.extend(root/name for name in ('pyproject.toml','README.md','LICENSE','.github/workflows/ci.yml'))
    return {str(p.relative_to(root)).replace('\\','/'):sha(p) for p in sorted(set(files))}


def stage_path(value):
    p=Path(value).resolve()
    if p.parent!=(ROOT/'evidence/w1').resolve() or not p.name.startswith('adapter-platform-'):
        raise ValueError('stage must be a direct owned adapter-platform evidence directory')
    return p


def linux_path(path):
    p=Path(path).resolve();drive=p.drive.rstrip(':').lower()
    if not drive: return str(p)
    return '/mnt/'+drive+'/'+str(p).replace('\\','/').split(':',1)[1].lstrip('/')


def temporary_root(folder,linux=None):
    if linux is None:linux=os.name!='nt'
    if not linux:return folder/'tmp'
    stage=next((p for p in (folder,*folder.parents) if p.name.startswith('adapter-platform-')),None)
    if stage is None:raise ValueError('native Linux temporary workspace needs an owned stage identity')
    namespace=Path('/tmp')/('anysolid-'+stage.name)
    result=namespace/folder.name
    if result.parent!=namespace or not namespace.name.startswith('anysolid-adapter-platform-'):
        raise ValueError('invalid owned Linux temporary prefix')
    return result


def environment(folder,work=None):
    env=dict(os.environ)
    for name in ('PYTHONPATH','PYTEST_ADDOPTS','PYTEST_PLUGINS','VIRTUAL_ENV','UV_PROJECT_ENVIRONMENT'):
        env.pop(name,None)
    temporary=temporary_root(folder);temporary.mkdir(exist_ok=True,parents=True)
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
        NUMBA_NUM_THREADS='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',
        UV_CACHE_DIR=str(folder.parent.parent/'cache-windows' if os.name=='nt' else temporary/'uv-cache'),
        PIP_CACHE_DIR=str(temporary/'pip-cache'),TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary))
    if work is not None:env['PYTHONPATH']=str(work)
    return env


def windows_supervisor():
    path=Path.home()/'bin/claude-review.py'
    spec=importlib.util.spec_from_file_location('_adapter_windows_supervisor',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def linux_members(sid):
    result=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            fields=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(fields[3])==sid:result.append({'pid':int(p.name),'state':fields[0]})
        except (FileNotFoundError,ProcessLookupError,PermissionError):pass
    return result


def reap():
    while True:
        try:
            pid,_=os.waitpid(-1,os.WNOHANG)
            if pid==0:return
        except ChildProcessError:return


def linux_process(command,folder,timeout,env,cwd):
    folder.mkdir(parents=True);started=time.perf_counter();process=None;status='startup_error';code=None;cleanup=None
    save(folder/'identity.json',{'command':command,'cwd':str(cwd),'timeout_seconds':timeout,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    try:
        with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            process=subprocess.Popen(command,cwd=cwd,env=env,stdout=out,stderr=err,start_new_session=True)
            save(folder/'owned-session.json',{'session_id':process.pid,'members_at_start':linux_members(process.pid)})
            try:code=process.wait(timeout=timeout);status='completed' if code==0 else 'process_error'
            except subprocess.TimeoutExpired:status='timeout'
            except BaseException:status='interrupted';raise
    finally:
        if process is not None:
            # Controller is a Linux child-subreaper. Descendants in this owned
            # session are killed/reaped even when their immediate parent exits.
            before=linux_members(process.pid)
            for member in before:
                try:os.kill(member['pid'],signal.SIGKILL)
                except ProcessLookupError:pass
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:pass
            until=time.perf_counter()+5
            while time.perf_counter()<until:
                reap();remaining=linux_members(process.pid)
                if not remaining:break
                time.sleep(.05)
            cleanup={'verified':not remaining,'session_id':process.pid,'members_before_cleanup':before,'remaining_members':remaining}
        else:cleanup={'verified':True,'session_id':None,'remaining_members':[]}
        receipt={'status':status,'exit_code':code,'process_wall_seconds':time.perf_counter()-started,'cleanup':cleanup}
        save(folder/'result.json',receipt)
    return receipt


def run_process(command,folder,timeout,env,cwd):
    if os.name=='nt':
        folder.mkdir(parents=True);receipt,_=windows_supervisor().run_process(command,folder,'stdout',timeout,env,cwd)
    else:receipt=linux_process(command,folder,timeout,env,cwd)
    if receipt['status']!='completed' or not receipt['cleanup']['verified']:
        raise RuntimeError(f'phase failed: {folder.name}: {receipt["status"]}')
    return receipt


def prepare():
    folder=ROOT/'evidence/w1'/('adapter-platform-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True);snapshot=folder/'source';snapshot.mkdir();inventory=source_inventory(ROOT)
    for name in inventory:
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    manifest={'scope':'local current-owner adapter CI snapshot, not clean checkout, not ANYsolver or physics qualification',
        'cells':list(CELLS),'source_sha256':inventory,'runner_sha256':sha(__file__),'test_process_budget_seconds':1200,
        'cell_timeout_seconds':300,'linux_cell_internal_seconds':280,'windows_pythons':WINDOWS_PYTHONS,
        'commands':['python -m pytest -q tests --junitxml=...','python -m build --outdir ...','python -m pip install --force-reinstall --no-deps built.whl','python -I tools/installed_smoke.py'],
        'linux_supervision':'Linux child-subreaper/start_new_session/session membership cleanup plus GNU timeout outer bound',
        'started_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    save(folder/'manifest.json',manifest);save(folder/'matrix.json',{'cells':{},'test_process_wall_seconds':0.,'complete':False})
    emit({'stage':str(folder),'manifest_sha256':sha(folder/'manifest.json'),'inputs':len(inventory),'cells':list(CELLS)})


def verify_source(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest['runner_sha256']!=sha(__file__):raise ValueError('matrix runner changed after snapshot')
    for name,digest in manifest['source_sha256'].items():
        if sha(folder/'source'/name)!=digest:raise ValueError('snapshot source changed: '+name)
    return manifest


def resolve_managed_interpreter(candidates):
    # uv may expose both a patch-version directory and a minor-version alias.
    # They are one interpreter only when their physical targets are identical.
    found=sorted({path.resolve() for path in candidates})
    if len(found)!=1:raise ValueError('managed Linux interpreter lookup ambiguous')
    return str(found[0])


def setup_cell(folder,cell):
    manifest=verify_source(folder);output=folder/'cells'/cell;output.mkdir(parents=True,exist_ok=True)
    if (output/'setup.json').exists():raise ValueError('cell setup already recorded; no automatic repeat')
    env=environment(output);uv=WINDOWS_UV if os.name=='nt' else LINUX_UV;version=cell[-3:];label='3.'+version[1:]
    if os.name=='nt':base=WINDOWS_PYTHONS[version]
    elif version in LINUX_PYTHONS:base=LINUX_PYTHONS[version]
    else:
        install=folder/'managed-python';env['UV_PYTHON_INSTALL_DIR']=str(install)
        run_process([uv,'python','install',label,'--install-dir',str(install),'--no-bin'],output/'setup-python',300,env,folder)
        base=resolve_managed_interpreter(install.glob('cpython-'+label+'*-linux-*/bin/python'+label))
    venv=output/'runtime';run_process([uv,'venv','--seed','--no-project','--no-python-downloads','--python',base,str(venv)],output/'setup-venv',300,env,folder)
    python=venv/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    setup_source=output/'setup-source';shutil.copytree(folder/'source',setup_source)
    run_process([uv,'pip','install','--python',str(python),str(setup_source)+'[skfem,test]','build'],output/'setup-dependencies',300,env,folder)
    run_process([str(python),'-m','pip','check'],output/'setup-dependency-check',60,env,folder)
    save(output/'setup.json',{'cell':cell,'base_python':base,'python':str(python),'manifest_sha256':sha(folder/'manifest.json')})
    emit({'cell':cell,'setup':'completed','python':str(python)})


RUNTIME_CODE="""
import importlib.metadata,json,sys,platform,tempfile,os
import anysolid
lazy=not {'skfem','anysolver'}&sys.modules.keys()
import numpy,scipy,scipy.linalg,skfem
from threadpoolctl import threadpool_info
versions={p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-fem','pytest','build','threadpoolctl')}
pools=threadpool_info()
assert lazy and pools and all(p['num_threads']==1 for p in pools)
print(json.dumps({'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'versions':versions,'pools':pools,'lazy_import':lazy,'installed_origin':anysolid.__file__,'temporary_root':tempfile.gettempdir(),'TMPDIR':os.environ.get('TMPDIR')}))
"""


def execute_cell(folder,cell):
    manifest=verify_source(folder);output=folder/'cells'/cell
    if (output/'cell.json').exists():raise ValueError('cell attempt already consumed; no automatic repeat')
    setup=json.loads((output/'setup.json').read_text());python=setup['python']
    if setup['manifest_sha256']!=sha(folder/'manifest.json'):raise ValueError('setup/source registration mismatch')
    work=output/'worktree';shutil.copytree(folder/'source',work);env=environment(output,work)
    started=time.perf_counter();deadline=started+280;phases={};status='failed';counts=None;artifacts={};error=None
    def phase(name,command,test=False):
        remaining=deadline-time.perf_counter()
        if remaining<=0:raise TimeoutError('cell deadline exhausted')
        receipt=run_process(command,output/name,min(remaining,300),env,work);phases[name]=receipt
        return receipt
    try:
        phase('runtime-probe',[python,'-I','-c',RUNTIME_CODE])
        phase('pytest',[python,'-m','pytest','-q','-p','no:cacheprovider','tests','--junitxml='+str(output/'pytest.xml')],True)
        suites=list(ET.parse(output/'pytest.xml').getroot().iter('testsuite'))
        counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
        if not counts['tests'] or any(counts[k] for k in ('failures','errors','skipped')):raise ValueError('test count/failure/skip gate')
        dist=output/'dist';phase('build',[python,'-m','build','--outdir',str(dist),str(work)])
        wheels=list(dist.glob('*.whl'));sdists=list(dist.glob('*.tar.gz'))
        if len(wheels)!=1 or len(sdists)!=1:raise ValueError('wheel/sdist artifact ambiguity')
        artifacts={p.name:sha(p) for p in wheels+sdists}
        phase('install-wheel',[python,'-m','pip','install','--force-reinstall','--no-deps',str(wheels[0])])
        phase('installed-smoke',[python,'-I',str(work/'tools/installed_smoke.py')],True)
        phase('installed-dependency-check',[python,'-m','pip','check'])
        if source_inventory(work)!=manifest['source_sha256']:raise ValueError('tracked input bytes changed during cell')
        status='passed'
    except BaseException as exc:error={'type':type(exc).__name__,'message':str(exc)}
    finally:
        if counts is None and (output/'pytest.xml').exists():
            suites=list(ET.parse(output/'pytest.xml').getroot().iter('testsuite'))
            counts={key:sum(int(s.attrib.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
        # Failed phases still count toward the shared test budget.
        test_wall=0.
        for name in ('pytest','installed-smoke'):
            path=output/name/'result.json'
            if path.exists():test_wall+=json.loads(path.read_text())['process_wall_seconds']
        record={'cell':cell,'status':status,'manifest_sha256':sha(folder/'manifest.json'),'counts':counts,
            'phase_receipts':{p.parent.name:str(p) for p in output.glob('*/result.json')},'artifacts_sha256':artifacts,'error':error,
            'test_process_wall_seconds':test_wall,'cell_wall_seconds':time.perf_counter()-started,
            'temporary_workspace':str(temporary_root(output)),
            'cleanup_verified':all(json.loads(p.read_text())['cleanup']['verified'] for p in output.glob('*/result.json'))}
        save(output/'cell.json',record);emit(record)
    return int(status!='passed')


def linux_initialize():
    if ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)!=0:raise OSError('Linux child-subreaper unavailable')
    signal.signal(signal.SIGTERM,lambda *args:(_ for _ in ()).throw(KeyboardInterrupt('owned Linux controller terminated')))


def relay(folder,cell,action):
    command=['wsl.exe','-d','Ubuntu-24.04','--','timeout','--signal=TERM','--kill-after=5s','295s','python3',linux_path(Path(__file__)),
             '_linux',action,'--stage',linux_path(folder),'--cell',cell]
    wrapper=folder/'relay'/f'{cell}-{action}';wrapper.mkdir(parents=True)
    receipt,_=windows_supervisor().run_process(command,wrapper,'stdout',300,dict(os.environ),ROOT)
    if receipt['status']!='completed' or not receipt['cleanup']['verified']:raise RuntimeError('WSL relay failed; inspect Linux receipt')


def run_matrix(folder,selected):
    verify_source(folder);ledger=json.loads((folder/'matrix.json').read_text())
    for cell in selected:
        if cell in ledger['cells']:raise ValueError('recorded cell may not be rerun automatically')
        if ledger['test_process_wall_seconds']>=1200:raise ValueError('cumulative1200s test-process budget exhausted')
        output=folder/'cells'/cell
        remaining=1200-ledger['test_process_wall_seconds']
        if remaining<300:raise ValueError('insufficient remaining budget for a300s bounded cell')
        try:
            if cell.startswith('linux'):relay(folder,cell,'run')
            else:execute_cell(folder,cell)
        except Exception as exc:emit({'cell':cell,'orchestration_error':str(exc)})
        receipt=output/'cell.json'
        if receipt.exists():
            data=json.loads(receipt.read_text());ledger['cells'][cell]=data;ledger['test_process_wall_seconds']+=data['test_process_wall_seconds']
        else:ledger['cells'][cell]={'cell':cell,'status':'missing_terminal_receipt','budget_status':'unknown_do_not_continue'}
        ledger['complete']=set(ledger['cells'])==set(CELLS) and all(r['status']=='passed' for r in ledger['cells'].values())
        save(folder/'matrix.json',ledger)
        emit({'cell':cell,'status':ledger['cells'][cell]['status'],'test_process_wall_cumulative':ledger['test_process_wall_seconds'],'matrix_complete':ledger['complete']})
        if not receipt.exists():break
    return int(any(c not in ledger['cells'] or ledger['cells'][c]['status']!='passed' for c in selected))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','setup','run','_linux','probe'))
    parser.add_argument('linux_action',nargs='?',choices=('setup','run','probe'));parser.add_argument('--stage');parser.add_argument('--cell',choices=CELLS)
    parser.add_argument('--cells',nargs='+',choices=CELLS,default=list(CELLS));args=parser.parse_args()
    if args.action=='prepare':prepare();return 0
    folder=stage_path(args.stage)
    if args.action=='_linux':
        linux_initialize()
        if args.linux_action=='setup':setup_cell(folder,args.cell);return 0
        if args.linux_action=='run':return execute_cell(folder,args.cell)
        if args.linux_action=='probe':
            probe=folder/'probes'/'linux-timeout'
            command=[sys.executable,'-c','import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]);time.sleep(60)']
            receipt=linux_process(command,probe,1,environment(folder/'probes'),folder)
            passed=receipt['status']=='timeout' and receipt['cleanup']['verified'] and len(receipt['cleanup']['members_before_cleanup'])>=2
            save(probe/'probe.json',{'passed':passed,'receipt':receipt});emit({'probe':'linux_timeout_descendant_cleanup','passed':passed,'receipt':receipt});return int(not passed)
    if args.action=='setup':
        if not args.cell:parser.error('--cell required')
        if args.cell.startswith('linux'):relay(folder,args.cell,'setup')
        else:setup_cell(folder,args.cell)
        return 0
    if args.action=='run':return run_matrix(folder,args.cells)
    if args.action=='probe':relay(folder,'linux312','probe');return 0
    raise ValueError('unsupported action')


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:emit({'status':'failed','error_type':type(exc).__name__,'error':str(exc)});raise SystemExit(1)
