"""Independent isolated consumers of one wheel target; never source imports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = Path(sys.argv[1]).resolve()
    if target.name != 'site-packages' or not (target / 'anysolid').is_dir():
        raise ValueError('explicit installed ANYsolid target required')
    scripts = ['installed_smoke.py', 'installed_host_smoke.py',
               'installed_trace_smoke.py', 'installed_coupling_smoke.py',
               'installed_revised_multiplier_smoke.py']
    bootstrap = ('import sys,runpy;sys.path.insert(0,sys.argv[1]);'
                 'runpy.run_path(sys.argv[2],run_name="__main__")')
    deadline = time.monotonic() + 80
    for name in scripts:
        script = ROOT / 'tools' / name
        command = [sys.executable, '-I', '-c', bootstrap, str(target), str(script)]
        print(json.dumps({'type': 'installed_check_start', 'script': name,
                          'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
                          'command': command}), flush=True)
        subprocess.run(command, cwd=target.parent, check=True,
                       timeout=max(0.01, min(20, deadline - time.monotonic())))
    print(json.dumps({'type': 'installed_snapshot_summary', 'passed': 5,
                      'target': str(target), 'source_pythonpath_ignored': True}), flush=True)


if __name__ == '__main__':
    main()
