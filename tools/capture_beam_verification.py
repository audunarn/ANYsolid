"""One bounded ordinary verification-report capture, preserving failed evidence."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import types
import uuid

ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'evidence/w1/platform-local-f41a6b6b84'
REPAIR_SHA='331136fe6056390d9f30f0e3b63610c1aed88388ecb42a9ab0a42283ec5fbe1d'
REMAINING_BEFORE_POLICY=714.6411203999742


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True),encoding='utf-8')


def child(folder):
    # Same public default function as the failed ordinary unit test. No case
    # selection, tolerance, material or solver control is changed.
    try:
        import anysolver,numba
        from threadpoolctl import threadpool_info
        if not Path(anysolver.__file__).resolve().is_relative_to(STAGE/'source/src'):
            raise ValueError('verification import escaped immutable staged host')
        pools=threadpool_info()
        if not pools or any(p['num_threads']!=1 for p in pools) or numba.config.DISABLE_JIT:
            raise ValueError('effective runtime/JIT changed')
        save(folder/'runtime.json',{'python':sys.version,'host_origin':anysolver.__file__,
            'actual_pools':pools,'numba':numba.__version__,'jit_disabled':bool(numba.config.DISABLE_JIT)})
        report=anysolver.run_beam_shell_verification()
        # Persist the complete returned report BEFORE interpreting or asserting
        # its status. Same JSON conversion as the public report writer.
        save(folder/'report.json',report)
        failures=[r for r in report['results'] if r['status']=='FAIL']
        save(folder/'summary.json',{'status':report['status'],'counts':report['counts'],
            'required_failures':report['required_failures'],'failed_cases':failures})
        print(json.dumps({'status':report['status'],'counts':report['counts'],
                          'required_failures':report['required_failures']}),flush=True)
        return 0 if report['status']=='passed' else 1
    except Exception as exc:
        save(folder/'capture-failure.json',{'type':type(exc).__name__,'error':str(exc),
            'report_retained':(folder/'report.json').exists()})
        traceback.print_exc();return 2


def capture(policy_evidence):
    path=ROOT/'tools/platform_local_repair.py';data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=REPAIR_SHA:raise ValueError('frozen repaired environment helper changed')
    module=types.ModuleType('_capture_frozen_repair');module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__)
    old,prior,runtime=module.stage_identity(STAGE)
    policy=Path(policy_evidence).resolve();receipt=json.loads((policy/'result.json').read_text())
    if (receipt['status'] not in ('completed','process_error') or receipt['exit_code'] not in (0,1)
            or receipt['cleanup']!={'verified':True,'active_processes':0}):
        raise ValueError('focused policy attempt lacks a clean terminal receipt')
    remaining=REMAINING_BEFORE_POLICY-receipt['process_wall_seconds']
    if remaining<250:raise ValueError('150s diagnostic plus100s reserve does not fit remaining budget')
    folder=ROOT/'evidence/w1'/('beam-report-diagnostic-'+uuid.uuid4().hex[:10]);folder.mkdir()
    work=folder/'workspace';work.mkdir();(folder/'portable-output').mkdir()
    env=module.environment(old,STAGE,folder)
    command=[sys.executable,str(Path(__file__).resolve()),'--child','--output',str(folder)]
    save(folder/'identity.json',{'command':command,'cwd':str(work),'capture_sha256':sha(__file__),
        'immutable_stage':str(STAGE),'old_runtime_sha256':sha(STAGE/'runtime.json'),
        'old_stage_identity_sha256':sha(STAGE/'identity.json'),'source_files_pinned':len(runtime['stage_source_test_sha256']),
        'source_report_sha256':sha(STAGE/'source/src/anysolver/beam_shell_verification.py'),
        'policy_evidence':str(policy),'policy_receipt_sha256':sha(policy/'result.json'),
        'policy_process_seconds':receipt['process_wall_seconds'],'policy_status':receipt['status'],
        'policy_exit_code':receipt['exit_code'],'remaining_before_diagnostic':remaining,
        'process_limit':150,'required_reserve':100,'environment':{k:v for k,v in env.items() if k.startswith('Q1M_') or k in runtime['environment']},
        'question':'Which required default public verification subcases failed under the unchanged staged candidate?',
        'alternatives':'baseline failure, runtime/context issue, or owner-overlay regression; status alone cannot discriminate',
        'decision':'Retain returned report before status checks; propose only a cause-specific owner repair. No third full portable retry/scientific campaign authority.'})
    helper=module.supervisor();result,_=helper.run_process(command,folder,'stdout',150,env,work)
    save(folder/'budget.json',{'previous_cumulative_seconds':2400-REMAINING_BEFORE_POLICY,
        'policy_seconds':receipt['process_wall_seconds'],'diagnostic_seconds':result['process_wall_seconds'],
        'remaining_seconds':remaining-result['process_wall_seconds'],'reserve_at_least100':remaining-result['process_wall_seconds']>=100,
        'cleanup':result['cleanup'],'protected_after':old.protected_hashes()})
    print(json.dumps({'evidence':str(folder),'receipt':result}),flush=True)
    return 0 if result['status']=='completed' else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--policy-evidence');p.add_argument('--child',action='store_true');p.add_argument('--output')
    a=p.parse_args()
    if a.child:return child(Path(a.output))
    if not a.policy_evidence:p.error('--policy-evidence is required')
    return capture(a.policy_evidence)


if __name__=='__main__':raise SystemExit(main())
