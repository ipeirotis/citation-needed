"""Independent key-based quotation grading; never use the tested checker as judge."""
import json
import re
import unicodedata


def equivalent(value):
    table = str.maketrans({'‘':"'",'’':"'",'“':'"','”':'"','ﬁ':'fi','ﬂ':'fl','ﬀ':'ff','ﬃ':'ffi','ﬄ':'ffl'})
    return ' '.join(unicodedata.normalize('NFC',value.translate(table)).split())


def grade_quotes(report, items, source):
    records = report.get('items', []) if isinstance(report,dict) else []
    if not isinstance(records,list):
        records = []
    out = []
    for item in items:
        found = [r for r in records if isinstance(r,dict) and r.get('id') == item['id']]
        record = found[0] if len(found) == 1 else {}
        verdict = record.get('verdict','missing')
        evidence = record.get('evidence','')
        evidence_ok = (isinstance(evidence,str) and len(evidence.split()) >= 4
                       and equivalent(evidence) in equivalent(item['context'])
                       and equivalent(item['original']) in equivalent(evidence))
        locator_ok = isinstance(record.get('source_location'),str) and item['paragraph_id'] in record['source_location']
        reason = record.get('reason','')
        reason_ok = isinstance(reason,str) and len(reason.split()) >= 3
        # A bare generic "manual review" is not a successful detection of a
        # known erroneous quotation, and absence does not become a true negative.
        correct = verdict == item['expected']
        out.append({'id':item['id'],'kind':item['kind'],'expected':item['expected'],
                    'given':verdict,'correct':correct,'evidence_ok':evidence_ok,
                    'locator_ok':locator_ok,'reason_present':reason_ok,
                    'item_passed':correct and evidence_ok and locator_ok and reason_ok,
                    'reason':reason,'context_review_required':item['kind'] in {'misleading_omission','benign_omission'}})
    invalid = [r for r in out if r['expected']=='invalid']
    valid = [r for r in out if r['expected']=='valid']
    duplicate_or_unknown = (len(records) != len(items) or
                           {r.get('id') for r in records if isinstance(r,dict)} != {i['id'] for i in items})
    return {'schema':'citation-needed.quotation-grade/1','items':out,
            'verdict_correct':sum(r['correct'] for r in out),'total':len(out),
            'errors_detected':sum(r['given']=='invalid' for r in invalid),'errors_total':len(invalid),
            'missed_or_unresolved_errors':sum(r['given']!='invalid' for r in invalid),
            'false_alarms':sum(r['given']=='invalid' for r in valid),'valid_total':len(valid),
            'unresolved_valid_items':sum(r['given'] not in {'valid','invalid'} for r in valid),
            'required_evidence_failures':sum(not (r['evidence_ok'] and r['locator_ok']) for r in out),
            'duplicate_or_unknown_records':duplicate_or_unknown,
            'passed':not duplicate_or_unknown and all(r['item_passed'] for r in out),
            'semantic_review':'Omission explanations require independent contextual review; keyword verdict agreement alone does not establish correct reasoning.'}
