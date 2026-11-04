"""Validate dataset integrity and evaluate the fixed checker, without an LLM."""
import argparse
import collections
import importlib.util
import json
import re
import sys
import time
import platform
from datetime import datetime, timezone
from pathlib import Path
from .build_dataset import DATA, ROOT, digest
from .grade import equivalent


def validate(data=DATA):
    manifest = json.loads((data/'manifest.json').read_text())
    keys = json.loads((data/'answer-key.json').read_text())
    checks = []
    def check(name, ok):
        checks.append({'check':name,'passed':bool(ok)})
    cases = manifest['cases']
    check('30 distinct manuscripts',len(cases)==30 and len({c['id'] for c in cases})==30)
    check('30 distinct real paper DOIs',len({c['doi'] for c in cases})==30)
    for case in cases:
        cid = case['id']
        source = (data/case['source']).read_bytes()
        manuscript = (data/case['manuscript']).read_bytes()
        items = keys[cid]
        check(cid+': source hash',digest(source)==case['source_sha256'])
        check(cid+': manuscript hash',digest(manuscript)==case['manuscript_sha256'])
        check(cid+': explicit redistribution license',bool(re.fullmatch(r'https?://creativecommons.org/licenses/by/(?:3\.0|4\.0)/?',case['license_url'])))
        check(cid+': six independent paragraph targets',len(items)==6 and len({i['paragraph_id'] for i in items})==6)
        check(cid+': 3 valid controls / 3 planted defects',collections.Counter(i['expected'] for i in items)=={'valid':3,'invalid':3})
        for i in items:
            check(cid+'/'+i['id']+': source-grounded review recorded',i.get('review_status','').startswith('source-grounded Codex review'))
            check(cid+'/'+i['id']+': original in source',i['original'] in source.decode())
            check(cid+'/'+i['id']+': context in source',i['context'] in source.decode())
            check(cid+'/'+i['id']+': mutation in manuscript',i['quote'] in manuscript.decode())
            check(cid+'/'+i['id']+': claim hash',digest(' '.join(i['claim'].split()).encode())[:12]==i['claim_hash'])
            check(cid+'/'+i['id']+': line locator',f'[{i["id"]}] The source states:' in manuscript.decode().splitlines()[i['line']-1])
            if i['kind'] in {'altered_number','altered_wording'}:
                check(cid+'/'+i['id']+': altered quote absent',equivalent(i['quote']) not in equivalent(source.decode()))
    return {'passed':all(c['passed'] for c in checks),'check_count':len(checks),'checks':checks}


def run_checker(data=DATA):
    started = time.perf_counter()
    spec = importlib.util.spec_from_file_location('tested_quote_checker',ROOT/'scripts/check_quotes.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = json.loads((data/'manifest.json').read_text())['cases']
    keys = json.loads((data/'answer-key.json').read_text())
    results = []
    for case in cases:
        source = (data/case['source']).read_text()
        normalized = module.normalize(source)
        for item in keys[case['id']]:
            r = module.check_quote(source,item['quote'],item['id'],normalized)
            results.append({'case':case['id'],'id':item['id'],'kind':item['kind'],
                            'truth':item['expected'],'expected_status':item['expected_checker_status'],
                            'actual_status':r['status'],'status_correct':r['status']==item['expected_checker_status'],
                            'found':r['found'],'context_decision':None,
                            'note':'mechanical presence result; manual_review is not a semantic detection'})
    counts = {}
    for row in results:
        c=counts.setdefault(row['kind'],{'total':0,'expected_status':0,'found':0,'not_found':0,'manual_review':0})
        c['total']+=1
        c['expected_status']+=int(row['status_correct'])
        c['found']+=int(row['found'])
        if row['actual_status'] in {'not_found','manual_review'}:c[row['actual_status']]+=1
    return {'schema':'quotation-checker-dataset-results/1','agent_runs':0,'items':results,'by_kind':counts,
            'ran_at_utc':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
            'elapsed_seconds':round(time.perf_counter()-started,6),
            'checker_sha256':digest((ROOT/'scripts/check_quotes.py').read_bytes()),
            'manifest_sha256':digest((data/'manifest.json').read_bytes()),
            'status_contract_passed':all(r['status_correct'] for r in results),
            'contextual_omission_accuracy':None,
            'limitations':['Not a Claude run or with/without-checker comparison.',
                           'Known mutation families; single publisher/year convenience sample.',
                           'Omission meaning is outside the script’s scope.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    validation=validate()
    results=run_checker()
    (args.output_dir/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    (args.output_dir/'checker-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'dataset_valid':validation['passed'],'dataset_checks':validation['check_count'],
                      'checker_status_contract_passed':results['status_contract_passed'],'by_kind':results['by_kind']},indent=2))
    sys.exit(0 if validation['passed'] and results['status_contract_passed'] else 1)
