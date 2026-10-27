"""Reviewed manual suffix continuation; never renew consumed study capacity."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
AMENDMENT=ROOT/'docs/extended_patch_continuation.json'


def main():
    amendment=json.loads(AMENDMENT.read_text())
    spec=importlib.util.spec_from_file_location('_frozen_extended_helpers',ROOT/'tools/extended_patch_study.py')
    study=importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    if amendment['state']!='REVIEWED_READY' or study.sha(__file__)!=amendment['resume_harness_sha256']:
        raise ValueError('continuation not ready or wrapper changed')
    base_path=ROOT/'docs/extended_patch_manifest.json'
    if study.sha(base_path)!=amendment['original_manifest_sha256']:
        raise ValueError('frozen original registration changed')
    original=json.loads(base_path.read_text())
    folder=ROOT/amendment['prefix_evidence']
    rows=[json.loads(line) for line in (folder/'stdout.jsonl').read_text().splitlines()]
    receipt=json.loads((folder/'result.json').read_text())
    if not receipt['cleanup']['verified'] or receipt['cleanup']['active_processes']!=0:
        raise ValueError('original process cleanup unverified')
    if rows[0]['manifest']!=original or rows[0]['harness_sha256']!=original['harness_sha256']:
        raise ValueError('prefix identity differs from original registration')
    summary=rows[-1]
    if summary['type']!='study_summary' or summary['case_attempts']!=4 or summary['execution_failures']!=1:
        raise ValueError('unexpected original terminal status')
    passed=[row for row in rows if row['type']=='case_result']
    prefix_ids=[row['case'] for row in passed]
    if (prefix_ids!=amendment['preserved_prefix_cases'] or
        any(not row['passed'] or not all(row['checks'].values()) for row in passed)):
        raise ValueError('prefix is not the registered passing prefix')
    starts=[row['case'] for row in rows if row['type']=='solve_start']
    if starts!=prefix_ids:
        raise ValueError('unexpected previous solve inventory')
    if amendment['remaining_process_seconds']+receipt['process_wall_seconds']>original['bounds']['process_tree_timeout_seconds']:
        raise ValueError('continuation would renew consumed process time')
    if amendment['remaining_attempt_slots']+summary['case_attempts']>original['bounds']['maximum_solves']:
        raise ValueError('continuation would renew consumed attempt slots')
    derived=copy.deepcopy(original)
    derived['cases']=[case for case in original['cases'] if case['id'] not in prefix_ids]
    if [case['id'] for case in derived['cases']]!=amendment['remaining_cases']:
        raise ValueError('continuation inventory differs from untouched suffix')
    coupling=amendment['product_delta']['path']
    if original['source_and_fixture_hashes'][coupling]!=amendment['product_delta']['old_sha256']:
        raise ValueError('original product delta identity mismatch')
    if study.sha(coupling)!=amendment['product_delta']['new_sha256']:
        raise ValueError('reviewed repair changed')
    derived['source_and_fixture_hashes'][coupling]=amendment['product_delta']['new_sha256']
    derived['inventory']={'solves':len(derived['cases']),'purpose':'unchanged registered suffix only'}
    derived['bounds']['maximum_solves']=amendment['remaining_attempt_slots']
    derived['bounds']['process_tree_timeout_seconds']=amendment['remaining_process_seconds']
    study.validate_manifest(derived)
    study.emit({'type':'continuation_identity','amendment':amendment,
                'amendment_sha256':study.sha(AMENDMENT),'derived_registration':derived,
                'preserved_prefix_evidence':str(folder),'consumed_process_seconds':receipt['process_wall_seconds']})
    import numpy as np
    import scipy
    import skfem
    if skfem.__version__!=original['runtime']['skfem']:
        raise ValueError('registered backend version changed')
    study.emit({'type':'runtime_identity','python':sys.version,'numpy':np.__version__,
                'scipy':scipy.__version__,'skfem':skfem.__version__})
    results=[]; attempts=0; failures=0
    for case in derived['cases']:
        study.emit({'type':'case_start','case':case['id'],'configuration':case})
        attempts+=1
        if attempts>amendment['remaining_attempt_slots']:
            raise ValueError('remaining attempt slots exhausted')
        started=time.perf_counter()
        try:
            result=study.run_case(np,case,derived,summary['case_attempts']+attempts)
            result['case_wall_seconds']=time.perf_counter()-started
            study.emit(result)
            results.append({key:result[key] for key in ('case','passed','checks','qualification',
                'primary_dofs','multiplier_rows','displacement_error_scaled','rotation_error_scaled',
                'energy_relative_error','stress_scaled_max','force_balance_scaled',
                'moment_balance_scaled','energy_work_error_scaled')})
        except Exception as exc:
            failures+=1
            study.emit({'type':'case_failure','case':case['id'],'error_type':type(exc).__name__,
                        'error':str(exc),'diagnostics':getattr(exc,'diagnostics',None)})
            traceback.print_exc(file=sys.stderr); break
    accepted=failures==0 and len(results)==len(derived['cases']) and all(row['passed'] for row in results)
    study.emit({'type':'continuation_summary','case_attempts':attempts,'case_results':len(results),
                'execution_failures':failures,'passed':accepted,'results':results,
                'preserved_prefix_count':len(prefix_ids),'production_status':'NO_GO_PRODUCTION_UNQUALIFIED'})
    return int(not accepted)


if __name__=='__main__':
    raise SystemExit(main())
