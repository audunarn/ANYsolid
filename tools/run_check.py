"""Local bounded checks with immutable attempt directories and full receipts."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    parser.add_argument('--cwd', default='C:/Github/ANYsolid')
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command
    if command and command[0] == '--':
        command = command[1:]
    if command[0] == 'python':
        command[0] = sys.executable
    root = Path(__file__).resolve().parents[1]
    folder = root/'evidence/w1'/f'{args.name}-{uuid.uuid4().hex[:10]}'
    folder.mkdir(parents=True)
    helper = Path.home()/'bin/claude-review.py'
    spec = importlib.util.spec_from_file_location('process_supervisor', helper)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join('C:/Github/'+name+'/src' for name in
        ('ANYsolid','ANYsolver','ANYmaterial','ANYmesh','ANYgeometry','ANYfileIO'))
    env['OMP_NUM_THREADS'] = '1'
    env['OPENBLAS_NUM_THREADS'] = '1'
    env['MKL_NUM_THREADS'] = '1'
    if '-m' in command and 'pytest' in command:
        command += ['--junitxml='+str(folder/'pytest.xml')]
    identity = {'command':command,'cwd':args.cwd,'python':sys.version,
                'pythonpath':env['PYTHONPATH'],'timeout_seconds':args.timeout,
                'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_hashes':{}}
    for repo in (root,Path('C:/Github/ANYsolver')):
        for path in (repo/'src').rglob('*.py'):
            if repo == root or path.name in ('solids.py','solid_trace.py','solid_residuals.py','assembly.py','matrix_assembly.py','e4_pl_element.py','elements.py','fe_core.py','__init__.py','modal.py','dynamics.py','nonlinear_static.py'):
                identity['source_hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    identity['input_hashes'] = {}
    for argument in command:
        name = argument.split('::',1)[0]
        path = Path(name)
        if not path.is_absolute():
            path = Path(args.cwd)/path
        if path.suffix=='.py' and path.is_file():
            identity['input_hashes'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = root/'docs/verification_registered_v2.json'
    if manifest.exists():
        identity['verification_manifest_sha256'] = hashlib.sha256(manifest.read_bytes()).hexdigest()
    supervisor.save(folder/'identity.json', identity)
    receipt,_ = supervisor.run_process(command,folder,'stdout',args.timeout,env,Path(args.cwd))
    print(json.dumps({'evidence':str(folder),**receipt}))
    return 0 if receipt['status']=='completed' else 1

if __name__=='__main__':
    sys.exit(main())
