"""Collect existing receipts; never rerun a check to reconstruct evidence."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
folder=root/'evidence/w1'
checks=[]
stages=[]
for path in sorted(folder.glob('*/identity.json')):
    identity=json.loads(path.read_text())
    if 'command' not in identity or 'cwd' not in identity:
        stages.append(str(path))
        continue
    receipt_path=path.parent/'result.json'
    receipt=json.loads(receipt_path.read_text()) if receipt_path.exists() else {'status':'missing_receipt'}
    record={'evidence':str(path.parent),'command':identity['command'],'cwd':identity['cwd'],
            'status':receipt['status'],'process_wall_seconds':receipt.get('process_wall_seconds')}
    if (path.parent/'pytest.xml').exists():
        xml=ET.parse(path.parent/'pytest.xml').getroot()
        suites=xml.findall('testsuite')
        record['pytest']={key:sum(int(s.attrib.get(key,0)) for s in suites)
                          for key in ('tests','failures','errors','skipped')}
    output=path.parent/'stdout.jsonl'
    if output.exists():
        for line in output.open(encoding='utf-8'):
            try:
                event=json.loads(line)
            except (ValueError,UnicodeError):
                continue
            if isinstance(event,dict) and event.get('type')=='run_summary':
                record['scientific_summary']=event
                if event.get('status')=='SCIENTIFIC_NO_GO' and event.get('execution_failures')==0:
                    record['semantic_outcome']='completed_scientific_target_failure'
            if isinstance(event,dict) and event.get('type')=='candidate_B_terminal':
                record['scientific_summary']={key:event[key] for key in
                    ('type','bounded_candidate_B_cases_met','execution_failures',
                     'fresh_case_attempts','fresh_metric_results','fresh_physical_results',
                     'fresh_reference_solves','validated_reused_reference_results',
                     'old_A_status','production_status') if key in event}
                if event.get('bounded_candidate_B_cases_met') is False:
                    record['semantic_outcome']='candidate_B_not_accepted'
            if isinstance(event,dict) and event.get('type')=='broader_terminal':
                record['scientific_summary']={key:event[key] for key in
                    ('type','passed','execution_failures','fresh_counts',
                     'fresh_completed_metric_physical_pairs','production_status') if key in event}
                if event.get('passed') is False:
                    record['semantic_outcome']=('completed_scientific_gate_failure'
                        if event.get('execution_failures')==0 else 'incomplete_construction_or_execution_failure')
            if isinstance(event,dict) and event.get('type')=='exact_retained_work_result':
                record['scientific_summary']={key:event[key] for key in
                    ('type','case','passed','normalized_error','unchanged_limit',
                     'original_double_status','FE_solves','production_status') if key in event}
            if isinstance(event,dict) and event.get('type')=='transition_terminal':
                record['scientific_summary']={key:event[key] for key in
                    ('type','passed','counts','execution_failures',
                     'reference_convergence_passed','production_status') if key in event}
                if event.get('passed') is False:
                    record['semantic_outcome']=('completed_scientific_gate_failure'
                        if event.get('execution_failures')==0 else 'incomplete_construction_or_execution_failure')
            if isinstance(event,dict) and event.get('type') in ('study_summary','continuation_summary'):
                record['scientific_summary']={key:event[key] for key in
                    ('type','passed','bounded_registered_cases_met','case_attempts','case_results',
                     'execution_failures','passed_registered_cases','metrics_completed',
                     'physical_results','references_completed','metric_cases',
                     'physical_rhs','host_factorizations') if key in event}
                passed=event.get('passed',event.get('bounded_registered_cases_met'))
                if passed is False:
                    record['semantic_outcome']=('completed_scientific_gate_failure' if event.get('execution_failures')==0
                                                else 'incomplete_construction_or_execution_failure')
    checks.append(record)
protected={}
baseline=Path('C:/ANYworkspaceWork/ANYsolid-20261026/baseline.json')
if baseline.exists():
    initial=json.loads(baseline.read_text())['ANYsolver']['dirty']
    for name in ('src/anysolver_results/__init__.py','src/anysolver_results/principals.py','tests/test_results_principal_axes.py'):
        path=Path('C:/Github/ANYsolver')/name
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        protected[name]={'sha256':digest,'unchanged_from_initial':initial.get(name)==digest}
summary={'status':'partial_implementation_NO_GO_coupling','checks':checks,
         'source_stage_identities':stages,
         'cumulative_recorded_check_process_wall_seconds':sum(r['process_wall_seconds'] or 0 for r in checks),
         'protected_dirty_work':protected,
         'wheel_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'dist').glob('*.whl')},
         'host_wheel_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (folder/'host-wheels').glob('*.whl')},
         'isolated_host_wheel_hashes':{str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in folder.glob('host-stage-*/source/dist/*.whl')},
         'remaining':'Repairedbeamfinitepatch accepted. Eightlocalownerplatformsnapshots pass; currentfullprofile331pass. Transitionreferencefielddifference.0029565802 failsunchanged.001, so coupledassessments0. FullhostCI/defaultreport remainfailed underrequiredNLG007warpedplasticrefusal. Cleancheckout/release andcurrentBcoupledperformance scope remainopen. Allhistoricalfailures preserved.'}
(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({'attempts':len(checks),'statuses':{status:sum(r['status']==status for r in checks)
                   for status in set(r['status'] for r in checks)},'protected_unchanged':all(r['unchanged_from_initial'] for r in protected.values())}))
