"""Separate retained-stage test-environment repair; no product or old evidence edits."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import types
import uuid

ROOT=Path(__file__).resolve().parents[1]
OLD_WRAPPER_SHA='fad2b2dffba5ffb9a60dff6cb7ac61de10e13be917cc6a316418e5c84801d909'
FOCUSED='tests/test_e4_pl_burnin.py::test_package_source_override_is_explicit_and_resolved'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):Path(path).write_text(json.dumps(value,indent=2),encoding='utf-8')


def load_old():
    path=ROOT/'tools/platform_local_checks.py';data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=OLD_WRAPPER_SHA:raise ValueError('old wrapper changed')
    module=types.ModuleType('_platform_frozen_preparation');module.__file__=str(path)
    exec(compile(data,str(path),'exec'),module.__dict__);return module


def supervisor():
    path=Path.home()/'bin/claude-review.py'
    spec=importlib.util.spec_from_file_location('_platform_process_supervisor',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def stage_identity(stage):
    old=load_old();stage=old.stage_path(stage);identity=json.loads((stage/'identity.json').read_text())
    runtime=json.loads((stage/'runtime.json').read_text());source=stage/'source'
    if identity['attempt_consumed'] is not True:raise ValueError('original consumed attempt must remain preserved')
    if Path(sys.executable).resolve()!=Path(identity['runtime_python']).resolve():raise ValueError('use audited isolated interpreter')
    for path,digest in runtime['stage_source_test_sha256'].items():
        if sha(source/path)!=digest:raise ValueError('retained staged source changed: '+path)
    if old.protected_hashes()!=identity['protected_working_files_before']:raise ValueError('protected dirty work changed')
    return old,identity,runtime


def environment(old,stage,folder):
    env=old.effective_environment(stage)
    env['RUNNER_TEMP']=str(folder/'portable-output')
    for name in ('ANYmaterial','ANYgeometry','ANYmesh','ANYfileIO'):
        path=ROOT.parent/name
        if not (path/'pyproject.toml').is_file():raise ValueError('missing explicit source owner: '+name)
        env['Q1M_'+name.upper()+'_ROOT']=str(path)
    env['Q1M_ANYSOLVER_ROOT']=str(stage/'source')
    return env


def prepare(stage):
    old,prior,runtime=stage_identity(stage);folder=ROOT/'evidence/w1'/('platform-local-repair-'+uuid.uuid4().hex[:10]);folder.mkdir()
    old_receipt=ROOT/'evidence/w1/platform-local-portable-2da6ea1ac8/result.json'
    old_execution=stage/'execution-result.json';used=json.loads(old_execution.read_text())['process_wall_seconds']
    if json.loads(old_receipt.read_text())['cleanup']!={'verified':True,'active_processes':0}:raise ValueError('old cleanup not verified')
    env=environment(old,stage,folder);(folder/'portable-output').mkdir()
    command=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',FOCUSED,
             '--junitxml='+str(folder/'focused.xml')]
    identity={'stage':str(stage),'old_wrapper_sha256':OLD_WRAPPER_SHA,'repair_sha256':sha(__file__),
        'old_identity_sha256':sha(stage/'identity.json'),'old_runtime_sha256':sha(stage/'runtime.json'),
        'old_outer_receipt_sha256':sha(old_receipt),'old_execution_sha256':sha(old_execution),
        'old_baseline':prior['host_baseline'],'old_canonical_process_wall_seconds':used,
        'source_test_files':len(runtime['stage_source_test_sha256']),
        'protected_before':old.protected_hashes(),'runtime_python':sys.executable,
        'focused_command':command,'environment':{k:v for k,v in env.items() if k.startswith('Q1M_') or k in runtime['environment']},
        'canonical_command':[sys.executable,'scripts/run_portable_ci.py','--workers','2','--timeout-seconds','1500'],
        'canonical_timeout_seconds':1500,'outer_timeout_seconds':1560,'cumulative_canonical_budget_seconds':2400,
        'execution_authorized':False,'new_full_attempt_consumed':False,
        'original_full_attempt_status':'FAILED_UNCHANGED',
        'scope':'ordinary Windows3.11 canonical source inventory environment repair; no scientific campaign authority'}
    save(folder/'identity.json',identity)
    focused=folder/'focused';focused.mkdir();helper=supervisor()
    receipt,_=helper.run_process(command,focused,'stdout',30,env,stage/'source')
    identity.update(focused_status=receipt['status'],focused_exit_code=receipt['exit_code'],
        focused_process_wall_seconds=receipt['process_wall_seconds'],
        remaining_after_focused_seconds=2400-used-receipt['process_wall_seconds'])
    save(folder/'identity.json',identity)
    print(json.dumps({'repair_evidence':str(folder),'focused_receipt':receipt,
        'execution_authorized':False,'portable_executed':False}))
    return 0 if receipt['status']=='completed' else 1


def run(folder):
    folder=Path(folder).resolve()
    if folder.parent!=(ROOT/'evidence/w1').resolve() or not folder.name.startswith('platform-local-repair-'):raise ValueError('unowned repair folder')
    identity=json.loads((folder/'identity.json').read_text());stage=Path(identity['stage'])
    old,prior,runtime=stage_identity(stage)
    if identity['execution_authorized'] is not True or identity['new_full_attempt_consumed'] is not False:raise ValueError('root GO absent or repair attempt consumed')
    if identity['repair_sha256']!=sha(__file__) or identity['old_identity_sha256']!=sha(stage/'identity.json') or identity['old_runtime_sha256']!=sha(stage/'runtime.json'):raise ValueError('repair/old identity changed')
    if (identity['old_outer_receipt_sha256']!=sha(ROOT/'evidence/w1/platform-local-portable-2da6ea1ac8/result.json')
            or identity['old_execution_sha256']!=sha(stage/'execution-result.json')):
        raise ValueError('preserved old process/budget evidence changed')
    if identity['focused_status']!='completed' or identity['focused_exit_code']!=0 or identity['remaining_after_focused_seconds']<1550:raise ValueError('focused gate/budget not satisfied')
    env=environment(old,stage,folder)
    if identity['environment']!={k:env[k] for k in identity['environment']}:raise ValueError('reviewed environment changed')
    identity['new_full_attempt_consumed']=True;save(folder/'identity.json',identity)
    start=time.perf_counter();helper=supervisor()
    full=folder/'full';full.mkdir()
    receipt,_=helper.run_process(identity['canonical_command'],full,'stdout',1560,env,stage/'source')
    save(folder/'terminal.json',{'status':receipt['status'],'exit_code':receipt['exit_code'],
        'canonical_process_wall_seconds':receipt['process_wall_seconds'],'repair_supervised_wall_seconds':time.perf_counter()-start,
        'old_canonical_seconds':identity['old_canonical_process_wall_seconds'],'focused_seconds':identity['focused_process_wall_seconds'],
        'cumulative_process_seconds':identity['old_canonical_process_wall_seconds']+identity['focused_process_wall_seconds']+receipt['process_wall_seconds'],
        'cleanup':receipt['cleanup'],'protected_after':old.protected_hashes(),'old_attempt':'FAILED_UNCHANGED','no_retry':True})
    print(json.dumps({'evidence':str(folder),'receipt':receipt}))
    return 0 if receipt['status']=='completed' else 1


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('prepare','run'));p.add_argument('--stage');p.add_argument('--repair')
    a=p.parse_args()
    if a.phase=='prepare':
        if not a.stage:p.error('--stage required')
        return prepare(Path(a.stage).resolve())
    if not a.repair:p.error('--repair required')
    return run(a.repair)


if __name__=='__main__':raise SystemExit(main())
