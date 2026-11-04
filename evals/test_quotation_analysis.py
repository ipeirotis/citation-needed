"""Analysis regressions: unknown outcomes, paired usage and tool receipts."""
import tempfile
import unittest
from pathlib import Path

from evals.quotation_benchmark.analyze_run import checker_coverage, summarize
from evals.quotation_benchmark.shared import sha


def run(case, condition, status, tokens):
    saved = status not in {'not_started','interrupted_no_record'}
    row = {'case':case,'condition':condition,'rep':1,'status':status,'record_saved':saved,
           'input_tokens':tokens if saved else None,'output_tokens':10 if saved else None,
           'cache_creation_input_tokens':0 if saved else None,'cache_read_input_tokens':0 if saved else None,
           'requests_receipted':1 if saved else None,'elapsed_seconds':5.0 if saved else None,
           'final_passed':False if saved else None}
    for version in ('original','regraded'):
        row.update({version+'_'+gate+'_pass':False if saved else None
                    for gate in ('archive','ledger','preservation','compliance')})
    return row


def target(row, expected='invalid'):
    completed = row['status']=='completed'
    return {'case':row['case'],'condition':row['condition'],'rep':1,'status':row['status'],
            'kind':'altered_wording','expected':expected,'given':expected if completed else None,
            'correct':True if completed else None,'evidence_ok':True if completed else None,
            'locator_ok':True if completed else None}


class AnalysisTests(unittest.TestCase):
    def test_unstarted_and_incomplete_are_unknown_not_wrong_verdicts(self):
        rows = [run('M01','checker-enabled','completed',100),
                run('M02','checker-enabled','incomplete_max_tokens',90),
                run('M03','checker-enabled','not_started',0),
                run('M04','checker-enabled','interrupted_no_record',0)]
        metrics = summarize(rows,[target(r) for r in rows])['conditions']['checker-enabled']
        self.assertEqual(metrics['planned_targets'],4)
        self.assertEqual(metrics['evaluated_targets'],1)
        self.assertEqual(metrics['correct_verdicts'],1)
        self.assertEqual(metrics['unknown_targets'],3)
        self.assertEqual(metrics['missed_errors_in_completed'],0)
        self.assertEqual(metrics['saved_records'],2)
        self.assertEqual(metrics['usage_receipted']['input_tokens'],190)

    def test_overhead_uses_only_complete_pairs(self):
        rows = [run('M01','checker-enabled','completed',100),
                run('M01','checker-disabled','completed',50),
                run('M02','checker-enabled','completed',1000000),
                run('M02','checker-disabled','incomplete_max_tokens',20)]
        metrics = summarize(rows,[target(r) for r in rows])
        self.assertEqual(metrics['pairs']['count'],1)
        self.assertEqual(metrics['pairs']['checker-enabled']['input_tokens'],100)
        self.assertEqual(metrics['pairs']['overhead_percent']['input_tokens'],100)
        self.assertEqual(metrics['conditions']['checker-enabled']['usage_receipted']['input_tokens'],1000100)

    def test_checker_receipt_allows_whitespace_but_not_fragment_or_wrong_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'source.txt').write_text('The value is not eight.\n')
            source_sha = sha((root/'source.txt').read_bytes())
            quote = 'The value\u00a0is not eight.'
            sent = 'The value is not eight.'
            call = {'type':'tool_use','id':'t1','name':'check_quotes',
                    'input':{'source_path':'source.txt','items':[{'id':'Q1','quote':sent}]}}
            messages = [{'role':'assistant','content':[call]},
                        {'role':'user','content':[{'type':'tool_result','tool_use_id':'t1','content':'{}'}]}]
            events = [{'operation':'read_file','path':'source.txt','sha256':source_sha},
                      {'operation':'check_quotes','path':'source.txt','quote_hashes':[sha(sent.encode())]}]
            def grade(q=quote, source=source_sha):
                return checker_coverage(root,messages,events,[{'id':'Q1','quote':q}],source,'checker-enabled')
            self.assertFalse(grade()['original'])
            self.assertTrue(grade()['regraded'])
            self.assertFalse(grade(quote+' …')['regraded'])
            self.assertFalse(grade(source='0'*64)['regraded'])
            events[1]['quote_hashes'] = ['0'*64]
            with self.assertRaisesRegex(AssertionError,'quotation receipt mismatch'):
                grade()


if __name__=='__main__':
    unittest.main()
