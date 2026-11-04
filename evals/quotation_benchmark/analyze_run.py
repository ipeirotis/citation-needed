"""Offline, read-only reanalysis of a quotation-run bundle; never calls a model.

Only code from this repository is executed. Uploaded analysis scripts are not
imported. Original files and grades are retained; outputs go to a new directory.
"""
import argparse
import csv
import json
import statistics
import subprocess
import types
from collections import Counter
from pathlib import Path

from .build_dataset import DATA, ROOT
from .grade import equivalent, grade_quotes
from .shared import grade_shared, safe_path, sha, snapshot

BASELINE = '919f9ec91deed4780f2fde0f46e585206e8757b0'
CONDITIONS = ('checker-enabled', 'checker-disabled')
USAGE = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def baseline_bytes(path):
    # This constant identifies trusted, published repository code. Never execute
    # code taken from the uploaded bundle or a revision supplied by the bundle.
    return subprocess.check_output(['git', 'show', BASELINE+':'+path], cwd=ROOT)


def baseline_shared():
    module = types.ModuleType('published_shared_v1')
    path = 'evals/quotation_benchmark/shared.py'
    exec(compile(baseline_bytes(path), BASELINE+':'+path, 'exec'), module.__dict__)
    return module.grade_shared


def checker_coverage(workspace, messages, events, keys, source_sha, condition):
    """Bind successful tool inputs to independently recorded source/check events.

    Typography/whitespace equivalence is allowed; words, numbers, fragments and
    different source bytes are not substituted for the required whole quotation.
    """
    results = {c['tool_use_id']: c for m in messages if m['role']=='user'
               and isinstance(m['content'], list) for c in m['content']
               if c.get('type')=='tool_result'}
    attempts = [c for m in messages if m['role']=='assistant' for c in m['content']
                if c.get('type')=='tool_use' and c.get('name')=='check_quotes']
    calls = [c for c in attempts if c['id'] in results and not results[c['id']].get('is_error')]
    receipts = [e for e in events if e.get('operation')=='check_quotes']
    assert len(calls)==len(receipts), 'checker-call receipt count mismatch'
    exact, normalized = set(), set()
    for call, event in zip(calls, receipts):
        args = call['input']
        assert args['source_path']==event['path'], 'checker source receipt mismatch'
        assert [sha(i['quote'].encode()) for i in args['items']]==event['quote_hashes'], 'checker quotation receipt mismatch'
        pos = next(i for i, e in enumerate(events) if e is event)
        previous = events[pos-1] if pos else {}
        actual = sha(safe_path(workspace, args['source_path']).read_bytes())
        assert previous.get('operation')=='read_file' and previous.get('path')==event['path'] and previous.get('sha256')==actual, 'checker read receipt mismatch'
        exact.update((actual, sha(i['quote'].encode())) for i in args['items'])
        normalized.update((actual, equivalent(i['quote'])) for i in args['items'])
    missing = [i['id'] for i in keys if (source_sha, equivalent(i['quote'])) not in normalized]
    old = all((source_sha, sha(i['quote'].encode())) in exact for i in keys)
    new = not missing
    if condition=='checker-disabled':
        old = new = not calls
        missing = []
    return {'original':old, 'regraded':new, 'missing_whole_quotations':missing,
            'calls':len(calls), 'attempts':len(attempts)}


def summarize(rows, item_rows):
    out = {'conditions':{}, 'pairs':{}, 'denominators':{
        'accuracy':'Correct verdicts / targets with an evaluable completed audit.',
        'planned_coverage':'Correct resolved targets / all planned targets; uncompleted targets remain unknown.',
        'gate_failures':'Report completed runs separately from all saved records.',
        'usage':'Receipted API usage only; interrupted requests without receipts are unknown.'}}
    for condition in CONDITIONS:
        rs = [r for r in rows if r['condition']==condition]
        done = [r for r in rs if r['status']=='completed']
        saved = [r for r in rs if r['record_saved']]
        its = [i for i in item_rows if i['condition']==condition]
        evaluated = [i for i in its if i['status']=='completed']
        counts = Counter(r['status'] for r in rs)
        d = {'planned_runs':len(rs), 'statuses':dict(counts), 'saved_records':len(saved),
             'completed_runs':len(done), 'planned_targets':len(its),
             'evaluated_targets':len(evaluated), 'unknown_targets':len(its)-len(evaluated),
             'correct_verdicts':sum(i['correct'] for i in evaluated),
             'errors_evaluated':sum(i['expected']=='invalid' for i in evaluated),
             'errors_detected':sum(i['given']=='invalid' and i['expected']=='invalid' for i in evaluated),
             'missed_errors_in_completed':sum(i['given']!='invalid' and i['expected']=='invalid' for i in evaluated),
             'valid_controls_evaluated':sum(i['expected']=='valid' for i in evaluated),
             'false_alarms':sum(i['given']=='invalid' and i['expected']=='valid' for i in evaluated),
             'evidence_or_locator_failures':sum(not i['evidence_ok'] or not i['locator_ok'] for i in evaluated),
             'final_passes':sum(r['final_passed'] is True for r in rs),
             'usage_receipted':{k:sum(r[k] or 0 for r in saved) for k in USAGE},
             'requests_receipted':sum(r['requests_receipted'] or 0 for r in saved),
             'recorded_elapsed_seconds':sum(r['elapsed_seconds'] or 0 for r in saved),
             'median_recorded_seconds':statistics.median(r['elapsed_seconds'] for r in saved) if saved else None,
             'gates':{}, 'types':{}}
        for version in ('original', 'regraded'):
            d['gates'][version] = {scope:{g:sum(r[version+'_'+g+'_pass'] is False for r in subset)
                for g in ('archive','ledger','preservation','compliance')}
                for scope, subset in (('completed',done),('saved',saved))}
        for kind in sorted({i['kind'] for i in its}):
            group = [i for i in evaluated if i['kind']==kind]
            d['types'][kind] = {'evaluated':len(group), 'correct':sum(i['correct'] for i in group),
                               'planned':sum(i['kind']==kind for i in its)}
        out['conditions'][condition] = d
    by_case = {}
    for r in rows:
        if r['status']=='completed':
            by_case.setdefault((r['case'],r['rep']),{})[r['condition']] = r
    pairs = [pair for pair in by_case.values() if all(k in pair for k in CONDITIONS)]
    p = {'count':len(pairs), 'cases':[{'case':x[CONDITIONS[0]]['case'], 'rep':x[CONDITIONS[0]]['rep']} for x in pairs]}
    for condition in CONDITIONS:
        subset = [x[condition] for x in pairs]
        p[condition] = {k:sum(r[k] for r in subset) for k in (*USAGE,'requests_receipted','elapsed_seconds')}
        p[condition]['median_seconds'] = statistics.median(r['elapsed_seconds'] for r in subset) if subset else None
    if pairs:
        a,b = (p[k] for k in CONDITIONS)
        p['overhead_percent'] = {k:100*(a[k]/b[k]-1) for k in ('input_tokens','output_tokens','requests_receipted','elapsed_seconds') if b[k]}
        p['difference_of_condition_medians_seconds'] = a['median_seconds']-b['median_seconds']
        p['median_within_pair_time_difference_seconds'] = statistics.median(x[CONDITIONS[0]]['elapsed_seconds']-x[CONDITIONS[1]]['elapsed_seconds'] for x in pairs)
    out['pairs'] = p
    return out


def analyze(main, reviews):
    main = Path(main)
    plan = read_json(main/'run-plan.json')
    manifest = read_json(DATA/'manifest.json')
    keys = read_json(DATA/'answer-key.json')
    cases = {c['id']:c for c in manifest['cases']}
    assert plan['skill_parent_commit']==BASELINE, 'unexpected experimental baseline'
    assert plan['source_manifest_sha256']==sha((DATA/'manifest.json').read_bytes())
    assert plan['answer_key_sha256']==sha((DATA/'answer-key.json').read_bytes())
    for name,digest in plan['benchmark_code_sha256'].items():
        assert sha(baseline_bytes('evals/quotation_benchmark/'+name))==digest, 'baseline code mismatch: '+name
    for path,field in [('SKILL.md','skill_sha256'),('scripts/check_quotes.py','checker_sha256')]:
        assert sha(baseline_bytes(path))==plan[field]==sha((ROOT/path).read_bytes())
    old_shared = baseline_shared()
    decisions = {(r['case'],r['condition'],r.get('rep',1),r['id']):r for r in reviews['decisions']}
    assert len(decisions)==len(reviews['decisions']), 'duplicate review decisions'
    rows, items, differences, integrity = [], [], [], []
    for number, run in enumerate(plan['runs'],1):
        case, condition, rep = run['case'], run['condition'], run['rep']
        folder = main/case/condition/f'rep{rep}'
        workspace = folder/'workspace'
        saved = (folder/'grading.json').is_file()
        record = read_json(folder/'grading.json') if saved else {}
        status = record.get('status','interrupted_no_record' if folder.exists() else 'not_started')
        row = dict(plan_order=number, case=case, condition=condition, rep=rep, status=status, record_saved=saved,
                   elapsed_seconds=record.get('elapsed_seconds'), requests_receipted=record.get('api_requests'),
                   **{k:record.get('usage',{}).get(k) for k in USAGE},
                   original_final_passed=None, final_passed=None, contextual_review=None, targets=len(keys[case]))
        if folder.exists():
            assert sha((workspace/'manuscript.md').read_bytes())==cases[case]['manuscript_sha256']
            assert sha((workspace/'source-input/source.txt').read_bytes())==cases[case]['source_sha256']
        qgrade = None
        if saved:
            before,after,events,contract = (read_json(folder/f) for f in ('before.json','after.json','tool-events.json','contract.json'))
            assert snapshot(workspace)==after, 'workspace/snapshot mismatch: '+case+' '+condition
            assert len(record['models_returned'])==1 and record['models_returned'][0]==plan['model']
            responses = read_json(folder/'responses.json')
            assert len(responses)==record['api_requests']
            assert sorted({r['model'] for r in responses})==record['models_returned']
            assert all(sum(r.get('usage',{}).get(k,0) for r in responses)==record['usage'][k] for k in USAGE)
            audit = read_json(workspace/'literature/quotation-audit.json') if (workspace/'literature/quotation-audit.json').is_file() else {}
            qgrade = grade_quotes(audit,keys[case],(workspace/'source-input/source.txt').read_text())
            assert qgrade==record['quotation_grade'], 'quotation grade not reproduced: '+case
            original = old_shared(workspace,contract,before,events)
            assert original==record['shared_grade'], 'original shared grade not reproduced: '+case
            shared = grade_shared(workspace,contract,before,events)
            coverage = checker_coverage(workspace,read_json(folder/'messages.json'),events,keys[case],cases[case]['source_sha256'],condition)
            assert coverage['original']==record['condition_compliance'], 'original compliance not reproduced'
            assert coverage['attempts']==record['checker_calls']
            for item in keys[case]:
                decision = decisions.get((case,condition,rep,item['id']))
                if decision:
                    judged = next(i for i in qgrade['items'] if i['id']==item['id'])
                    for field,value in [('source_sha256',cases[case]['source_sha256']),
                                        ('quote_sha256',sha(item['quote'].encode())),
                                        ('context_sha256',sha(item['context'].encode())),
                                        ('explanation_sha256',sha(judged['reason'].encode()))]:
                        assert decision[field]==value, 'review bound to different evidence: '+case+' '+item['id']
            accepted = all(decisions.get((case,condition,rep,i['id']),{}).get('decision')=='accept'
                           for i in keys[case] if i['kind'] in {'benign_omission','misleading_omission'})
            for version,graded in [('original',original),('regraded',shared)]:
                row.update({version+'_'+g+'_pass':v['passed'] for g,v in graded['groups'].items()})
                row[version+'_compliance_pass'] = coverage[version]
            row.update(verdict_correct=qgrade['verdict_correct'] if status=='completed' else None,
                       contextual_review='accepted' if accepted else 'pending',
                       original_final_passed=status=='completed' and qgrade['passed'] and original['passed'] and coverage['original'] and accepted,
                       final_passed=status=='completed' and qgrade['passed'] and shared['passed'] and coverage['regraded'] and accepted)
            differences.append({'case':case,'condition':condition,'rep':rep,'status':status,
                'original_failures':{g:[c['check'] for c in v['checks'] if not c['passed']] for g,v in original['groups'].items()},
                'regraded_failures':{g:[c['check'] for c in v['checks'] if not c['passed']] for g,v in shared['groups'].items()},
                'compliance':coverage})
            integrity.append({'case':case,'condition':condition,'rep':rep,
                'original_quotation_grade_reproduced':True,'original_shared_grade_reproduced':True,
                'original_compliance_reproduced':True,'workspace_snapshot_matches':True,
                'usage_receipts_match':True,
                'artifact_sha256':{f:sha((folder/f).read_bytes()) for f in
                    ('grading.json','contract.json','before.json','after.json','responses.json','messages.json','tool-events.json')}})
        for item in keys[case]:
            judged = next((i for i in qgrade['items'] if i['id']==item['id']),{}) if qgrade else {}
            evaluable = status=='completed'
            items.append({'case':case,'condition':condition,'rep':rep,'id':item['id'],'kind':item['kind'],
                'expected':item['expected'],'status':status,
                **{k:judged.get(k) if evaluable else None for k in ('given','correct','evidence_ok','locator_ok','reason_present')},
                'context_review':decisions.get((case,condition,rep,item['id']),{}).get('decision') if evaluable and judged.get('context_review_required') else None})
        rows.append(row)
    assert len(rows)==plan['agent_runs_planned']
    return rows,items,differences,{'baseline_commit':BASELINE,'run_plan':plan,'records':integrity,
        'unreceipted_request_usage':'Unknown; no zero-token or zero-cost assumption.',
        'new_grader_sha256':{p.name:sha(p.read_bytes()) for p in (Path(__file__),Path(__file__).with_name('shared.py'),Path(__file__).with_name('grade.py'))}}


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-root',type=Path,required=True,help='original extracted main/ directory')
    parser.add_argument('--reviews',type=Path,required=True,help='reviewer-owned omission decisions')
    parser.add_argument('--output-dir',type=Path,required=True,help='new directory; original evidence is never edited')
    parser.add_argument('--bundle',type=Path,help='optional original ZIP to hash for provenance')
    args = parser.parse_args(argv)
    if args.output_dir.exists() or args.output_dir.resolve().is_relative_to(args.run_root.resolve()):
        parser.error('choose a new output directory outside the original run')
    reviews = read_json(args.reviews)
    rows,items,differences,integrity = analyze(args.run_root,reviews)
    if args.bundle:
        integrity['original_bundle_sha256'] = sha(args.bundle.read_bytes())
    args.output_dir.mkdir(parents=True)
    write_csv(args.output_dir/'results.csv',rows)
    write_csv(args.output_dir/'item-results.csv',items)
    write_json(args.output_dir/'metrics.json',summarize(rows,items))
    write_json(args.output_dir/'regrading.json',differences)
    write_json(args.output_dir/'integrity.json',integrity)
    write_json(args.output_dir/'context-review.json',reviews)
    print('Offline reanalysis saved; '+str(len(rows))+' planned runs, '+str(len(items))+' planned targets. No model calls.')


if __name__=='__main__':
    main()
