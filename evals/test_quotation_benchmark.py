"""Adversarial checker/grader tests. Synthetic workspaces are NOT Claude results."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from evals.quotation_benchmark.build_dataset import DATA, ROOT
from evals.quotation_benchmark.grade import grade_quotes
from evals.quotation_benchmark.runner import FileTools, definitions, execute, now, prepare
from evals.quotation_benchmark.shared import claim_hash, grade_shared, parse_ledger, sha, snapshot
from evals.quotation_benchmark.validate import validate


def fixture(target, case_id='M01', condition='checker-enabled'):
    case=next(c for c in json.loads((DATA/'manifest.json').read_text())['cases'] if c['id']==case_id)
    keys=json.loads((DATA/'answer-key.json').read_text())[case_id]
    root,contract,before=prepare(case,condition,target,keys)
    identity=sha(case['doi'].encode())[:8]
    archive=f'literature/sources/source--{case["doi"].replace("/","_")}-{identity}.txt'
    (root/'literature/sources').mkdir()
    (root/archive).write_bytes((root/'source-input/source.txt').read_bytes())
    entries=[]
    for item in keys:
        fields={'claim':json.dumps(item['claim'],ensure_ascii=False),'claim-hash':claim_hash(item['claim']),
          'source':'doi:'+case['doi'],'version-read':'version of record — supplied JATS prose extraction',
          'archived':archive+' sha256:'+case['source_sha256'],'license':'CC-BY-4.0',
          'updates':'check failed (offline supplied-source benchmark)',
          'verdict':'supported' if item['expected']=='valid' else 'unsupported',
          'evidence':json.dumps(item['original'],ensure_ascii=False)+' ('+item['paragraph_id']+')',
          'notes':'Synthetic output used only to test the graders.'}
        heading=f'cite:source — manuscript.md:{item["line"]}'
        entries.append('## ['+now()+'] '+heading+'\n'+'\n'.join(k+': '+v for k,v in fields.items())+'\n\n')
    ledger=contract['ledger_prefix']+''.join(entries)
    (root/contract['ledger']).write_text(ledger)
    if contract['companion']:
        _,parsed=parse_ledger(ledger)
        (root/contract['companion']).write_text(''.join(json.dumps(e,ensure_ascii=False)+'\n' for e in parsed))
    events=[{'operation':'read_file','path':'source-input/source.txt','sha256':case['source_sha256']}]
    return root,contract,before,events,case,keys


class SharedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root,self.contract,self.before,self.events,self.case,self.keys=fixture(Path(self.tmp.name)/'case')

    def grade(self):
        return grade_shared(self.root,self.contract,self.before,self.events)

    def test_compliant_local_run_passes_all_three(self):
        self.assertTrue(self.grade()['passed'])

    def test_missing_archive_fails_even_when_ledger_present(self):
        next((self.root/'literature/sources').iterdir()).unlink()
        r=self.grade()
        self.assertFalse(r['groups']['archive']['passed'])
        self.assertTrue(r['groups']['ledger']['passed'])

    def test_self_hashed_quotes_only_archive_is_rejected(self):
        p=next((self.root/'literature/sources').iterdir())
        p.write_text(self.keys[0]['original'])
        lp=self.root/self.contract['ledger']
        lp.write_text(lp.read_text().replace(self.case['source_sha256'],sha(p.read_bytes())))
        self.assertFalse(self.grade()['groups']['archive']['passed'])

    def test_read_trace_cannot_be_replaced_by_self_report(self):
        self.events=[]
        self.assertFalse(self.grade()['groups']['archive']['passed'])

    def test_wrong_hash_and_missing_license_fail(self):
        p=self.root/self.contract['ledger']
        p.write_text(p.read_text().replace('license: CC-BY-4.0','license: n/a').replace(self.case['source_sha256'],'a'*64))
        self.assertFalse(self.grade()['groups']['archive']['passed'])

    def test_claim_hash_mismatch_fails(self):
        p=self.root/self.contract['ledger']
        p.write_text(p.read_text().replace(self.keys[0]['claim_hash'],'0'*12))
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_ledger_must_match_reported_task_verdict(self):
        self.contract['items'][0]['reported_verdict']='unverifiable'
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_wrong_or_invalid_timestamp_fails(self):
        p=self.root/self.contract['ledger']
        p.write_text(p.read_text().replace(now().split('T')[0]+'T','not-a-dateT'))
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_backdated_fresh_entry_fails_run_window(self):
        self.contract['started_at']='2099-01-01T00:00:00Z'
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_existing_historical_entry_is_retained_but_not_fresh(self):
        p=self.root/self.contract['ledger']
        historical=('## [2020-01-01T00:00Z] cite:old — old.md:1\n'
                    'claim: "Historical claim."\nsource: doi:10.0000/old\n\n')
        current=p.read_text()
        prefix=self.contract['ledger_prefix']
        self.contract['ledger_prefix']=prefix+historical
        p.write_text(prefix+historical+current[len(prefix):])
        self.contract['started_at']=now()
        self.assertTrue(self.grade()['passed'])

    def test_removing_existing_header_fails(self):
        p=self.root/self.contract['ledger']
        p.write_text(p.read_text().replace('maintained-by: citation-needed skill','maintained-by: changed'))
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_missing_claim_entry_fails(self):
        p=self.root/self.contract['ledger']
        p.write_text(p.read_text().rsplit('## [',1)[0])
        self.assertFalse(self.grade()['groups']['ledger']['passed'])

    def test_original_manuscript_modification_fails(self):
        with (self.root/'manuscript.md').open('a') as f:f.write('changed')
        self.assertFalse(self.grade()['groups']['preservation']['passed'])

    def test_unexpected_output_fails(self):
        (self.root/'unexpected.txt').write_text('wrong location')
        self.assertFalse(self.grade()['groups']['preservation']['passed'])

    def test_archive_symlink_is_rejected(self):
        p=next((self.root/'literature/sources').iterdir())
        p.unlink()
        p.symlink_to(self.root/'source-input/source.txt')
        self.assertFalse(self.grade()['groups']['archive']['passed'])

    def test_opt_in_jsonl_matches_and_then_corruption_fails(self):
        root,c,b,e,_,_=fixture(Path(self.tmp.name)/'companion','M03')
        self.assertTrue(grade_shared(root,c,b,e)['passed'])
        (root/c['companion']).write_text('{}\n')
        self.assertFalse(grade_shared(root,c,b,e)['groups']['ledger']['passed'])

    def test_bibliography_archive_exemption_is_explicit(self):
        self.contract['archive_required']=False
        r=self.grade()
        self.assertTrue(r['groups']['archive']['passed'])
        self.assertIn('not-applicable',[x['check'] for x in r['groups']['archive']['checks']])

    def test_correct_doi_with_annotation_preserves_identity(self):
        p=self.root/self.contract['ledger']
        identity='doi:'+self.case['doi']
        p.write_text(p.read_text().replace('source: '+identity+'\n','source: '+identity+' (supplied source; registrar offline)\n'))
        self.assertTrue(self.grade()['passed'])

    def test_doi_matching_rejects_prefix_collision_and_ambiguity(self):
        from evals.quotation_benchmark.shared import source_matches
        expected='doi:10.1371/journal.pone.0291713'
        self.assertTrue(source_matches(expected+' (version of record)',expected))
        self.assertTrue(source_matches('https://doi.org/10.1371/journal.pone.0291713',expected))
        self.assertFalse(source_matches(expected+'99',expected))
        self.assertFalse(source_matches(expected+' or doi:10.1371/journal.pone.9999999',expected))
        self.assertFalse(source_matches('possibly '+expected,expected))


class QuotationGraderTests(unittest.TestCase):
    def setUp(self):
        self.keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        self.source=(DATA/'sources/M01.txt').read_text()
        self.report={'items':[{'id':i['id'],'verdict':i['expected'],'evidence':i['original'],
                     'source_location':i['paragraph_id'],'reason':'Specific explanation of the source comparison.'} for i in self.keys]}

    def test_keyed_response_with_evidence_passes_mechanical_grade(self):
        self.assertTrue(grade_quotes(self.report,self.keys,self.source)['passed'])

    def test_review_does_not_count_as_correct_error_detection(self):
        for i in self.report['items']:i['verdict']='review'
        r=grade_quotes(self.report,self.keys,self.source)
        self.assertEqual(r['errors_detected'],0)
        self.assertEqual(r['missed_or_unresolved_errors'],3)
        self.assertFalse(r['passed'])

    def test_missing_evidence_fails_even_with_correct_verdict(self):
        self.report['items'][0]['evidence']=''
        r=grade_quotes(self.report,self.keys,self.source)
        self.assertEqual(r['verdict_correct'],6)
        self.assertFalse(r['passed'])

    def test_irrelevant_real_source_quote_does_not_satisfy_evidence(self):
        self.report['items'][0]['evidence']=self.keys[1]['original']
        self.assertFalse(grade_quotes(self.report,self.keys,self.source)['passed'])

    def test_all_invalid_has_false_alarms(self):
        for i in self.report['items']:i['verdict']='invalid'
        self.assertEqual(grade_quotes(self.report,self.keys,self.source)['false_alarms'],3)

    def test_duplicate_or_extra_item_fails(self):
        self.report['items'].append(copy.deepcopy(self.report['items'][0]))
        self.assertFalse(grade_quotes(self.report,self.keys,self.source)['passed'])


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_ablation_removes_only_checker_routes_and_script(self):
        case=json.loads((DATA/'manifest.json').read_text())['cases'][0]
        keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        root,_,_=prepare(case,'checker-disabled',Path(self.tmp.name)/'disabled',keys)
        self.assertFalse((root/'.claude/skills/citation-needed/scripts/check_quotes.py').exists())
        for p in (root/'.claude/skills/citation-needed').rglob('*.md'):
            self.assertNotIn('quotation-checks.md',p.read_text())
        self.assertEqual((root/'.claude/skills/citation-needed/references/source-archive.md').read_bytes(),(ROOT/'references/source-archive.md').read_bytes())
        self.assertEqual((root/'.claude/skills/citation-needed/references/verification-ledger.md').read_bytes(),(ROOT/'references/verification-ledger.md').read_bytes())
        self.assertNotIn('check_quotes',[x['name'] for x in definitions('checker-disabled')])

    def test_path_traversal_and_input_writes_are_denied(self):
        root=Path(self.tmp.name)
        (root/'manuscript.md').write_text('original')
        tools=FileTools(root,'checker-enabled')
        for path in ['../outside','/tmp/outside','manuscript.md']:
            with self.assertRaises(ValueError):tools.call('write_file',{'path':path,'content':'bad'})
        self.assertEqual((root/'manuscript.md').read_text(),'original')

    def test_no_completion_can_masquerade_as_pass(self):
        case=json.loads((DATA/'manifest.json').read_text())['cases'][0]
        keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        def fake_transport(key,body):
            self.assertNotIn('answer-key',json.dumps(body))
            return {'model':'stub-not-a-real-model','usage':{'input_tokens':7,'output_tokens':2},
                    'content':[{'type':'text','text':'Synthetic incomplete answer.'}],'stop_reason':'end_turn'}
        r=execute(case,'checker-enabled',Path(self.tmp.name)/'stub',keys,'not-a-key','stub-not-a-real-model',transport=fake_transport)
        self.assertFalse(r['mechanical_overall_passed'])
        self.assertEqual(r['usage']['input_tokens'],7)
        self.assertEqual(r['final_grade'],'FAIL')

    def test_no_credentials_do_not_create_real_run_results(self):
        from unittest.mock import patch
        from evals.quotation_benchmark.runner import main
        output=Path(self.tmp.name)/'not-run'
        with patch.dict('os.environ',{},clear=True):
            self.assertEqual(main(['--output-dir',str(output),'--cases','M01']),2)
        self.assertFalse(output.exists())

    def test_disabled_tool_is_unavailable(self):
        tool=FileTools(Path(self.tmp.name),'checker-disabled')
        with self.assertRaises(ValueError):
            tool.call('check_quotes',{'source_path':'source-input/source.txt','items':[]})

    def test_checker_use_is_bound_to_actual_source_bytes(self):
        case=json.loads((DATA/'manifest.json').read_text())['cases'][0]
        keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        root,_,_=prepare(case,'checker-enabled',Path(self.tmp.name)/'binding',keys)
        tool=FileTools(root,'checker-enabled')
        tool.call('check_quotes',{'source_path':'manuscript.md','items':[{'id':keys[0]['id'],'quote':keys[0]['quote']}]})
        from evals.quotation_benchmark.grade import equivalent
        self.assertNotIn((case['source_sha256'],equivalent(keys[0]['quote'])),tool.checked_quotes)
        tool.call('check_quotes',{'source_path':'source-input/source.txt','items':[{'id':keys[0]['id'],'quote':keys[0]['quote']}]})
        self.assertIn((case['source_sha256'],equivalent(keys[0]['quote'])),tool.checked_quotes)

    def test_checker_compliance_allows_only_prototype_formatting_equivalents(self):
        from evals.quotation_benchmark.grade import equivalent
        case=json.loads((DATA/'manifest.json').read_text())['cases'][0]
        keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        root,_,_=prepare(case,'checker-enabled',Path(self.tmp.name)/'spaces',keys)
        tool=FileTools(root,'checker-enabled')
        item=next(x for x in keys if x['kind']=='formatting')
        self.assertIn('\u00a0',item['quote'])
        ordinary=item['quote'].replace('\u00a0',' ')
        tool.call('check_quotes',{'source_path':'source-input/source.txt','items':[{'id':item['id'],'quote':ordinary}]})
        self.assertIn((case['source_sha256'],equivalent(item['quote'])),tool.checked_quotes)
        self.assertNotEqual(equivalent('did not improve'),equivalent('did improve'))
        self.assertNotEqual(equivalent('32.5'),equivalent('32.6'))

    def test_file_tools_expose_real_line_numbers_without_altering_text(self):
        root=Path(self.tmp.name)
        (root/'manuscript.md').write_text('alpha\nbeta\ngamma\n')
        tools=FileTools(root,'checker-disabled')
        value=tools.call('read_file',{'path':'manuscript.md','start':6,'length':10})
        self.assertEqual(value['text'],'beta\ngamma')
        self.assertEqual(value['line_map'],[{'line':2,'start':6},{'line':3,'start':11}])
        hit=tools.call('search_file',{'path':'manuscript.md','query':'gamma'})
        self.assertEqual(hit['hits'][0]['match_line'],3)
        legacy=FileTools(root,'checker-disabled',line_numbers=False).call('read_file',{'path':'manuscript.md'})
        self.assertEqual(set(legacy),{'text','start','total_chars'})

    def test_remote_disconnect_saves_partial_evidence_without_retry(self):
        import http.client
        case=json.loads((DATA/'manifest.json').read_text())['cases'][0]
        keys=json.loads((DATA/'answer-key.json').read_text())['M01']
        attempts=[]
        def fake(key,body):
            attempts.append(1)
            if len(attempts)>1:raise http.client.RemoteDisconnected('provider closed connection')
            return {'model':'stub-not-a-real-model','usage':{'input_tokens':7,'output_tokens':3},
                'stop_reason':'tool_use','content':[{'type':'tool_use','id':'stub-call',
                'name':'read_file','input':{'path':'source-input/source.txt','length':50}}]}
        target=Path(self.tmp.name)/'disconnect'
        result=execute(case,'checker-enabled',target,keys,'not-a-key','stub-not-a-real-model',transport=fake)
        self.assertEqual(len(attempts),2)
        self.assertEqual(result['status'],'execution_error')
        self.assertEqual(result['api_requests'],1)
        self.assertEqual(result['api_requests_attempted'],2)
        self.assertEqual(result['unaccounted_requests'],1)
        self.assertFalse(result['usage_complete'])
        self.assertEqual(result['usage']['input_tokens'],7)
        self.assertTrue((target/'responses.json').exists())
        self.assertTrue((target/'tool-events.json').exists())
        self.assertTrue((target/'grading.json').exists())

    def test_provider_disconnect_is_converted_to_safe_diagnostic(self):
        import http.client
        from unittest.mock import patch
        from evals.quotation_benchmark.runner import api_request, ProviderRequestError
        with patch('urllib.request.urlopen',side_effect=http.client.RemoteDisconnected('sensitive provider detail')):
            with self.assertRaises(ProviderRequestError) as caught:api_request('not-a-key',{})
        self.assertNotIn('sensitive provider detail',str(caught.exception))


class DatasetTests(unittest.TestCase):
    def test_all_source_hashes_and_item_locations(self):
        self.assertTrue(validate()['passed'])


if __name__=='__main__':
    unittest.main()
