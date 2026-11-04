"""Reusable mechanical checks for a local citation-needed evaluation workspace.

The contract and before snapshot MUST be retained by the evaluator, outside the
agent workspace. Cloud stores and semantic judgments are deliberately not claimed.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def claim_hash(value):
    return sha(' '.join(value.split()).encode())[:12]


def source_matches(value, expected):
    """Recognize one unambiguous DOI with optional human-readable annotation.

    Identity is not field-string equality. A different/second DOI, a prefix
    collision or a bare mention in prose is not accepted as the cited identity.
    Non-DOI locators retain exact matching in this local profile.
    """
    value=value.strip()
    if not expected.lower().startswith('doi:'):
        return value==expected
    doi=expected[4:]
    pattern=r'^(?:doi:\s*|https?://(?:dx\.)?doi\.org/)'+re.escape(doi)+r'(?=\s|$)'
    if not re.match(pattern,value,re.I):
        return False
    identifiers=re.findall(r'\b10\.\d{4,9}/[^\s<>`]+',value,re.I)
    return all(x.rstrip('.,;').lower()==doi.lower() for x in identifiers)


def snapshot(root):
    root = Path(root)
    out = {}
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root).as_posix()
        if p.is_symlink():
            out[rel] = {'kind': 'symlink', 'target': str(p.readlink())}
        elif p.is_file():
            out[rel] = {'kind': 'file', 'sha256': sha(p.read_bytes()),
                        'mode': p.stat().st_mode & 0o777}
    return out


def safe_path(root, rel):
    """Refuse traversal, absolute paths and symlinks, including dangling ones."""
    root = Path(root).resolve()
    p = Path(rel)
    if p.is_absolute() or not p.parts or '..' in p.parts:
        raise ValueError('not a safe repository-relative path')
    current = root
    for part in p.parts:
        current /= part
        if current.is_symlink():
            raise ValueError('symlink path forbidden')
    if not current.resolve().is_relative_to(root):
        raise ValueError('path escapes workspace')
    return current


def parse_ledger(value):
    """Parse exact skill field labels and repeatable indented lead blocks."""
    lines = value.splitlines()
    starts = [i for i, s in enumerate(lines) if s.startswith('## [')]
    header_end = starts[0] if starts else len(lines)
    header = {}
    for s in lines[:header_end]:
        m = re.match(r'^([a-z][a-z-]*):\s*(.*)', s)
        if m:
            header[m[1]] = m[2].split('<!--')[0].strip()
    entries = []
    for pos, start in enumerate(starts):
        stop = starts[pos+1] if pos+1 < len(starts) else len(lines)
        m = re.fullmatch(r'## \[([^]]+)\] (.+)', lines[start])
        if not m:
            raise ValueError('malformed ledger heading')
        heading = m[2]
        entry = {'ts': m[1], 'type': re.split(r'[: —]', heading, maxsplit=1)[0], 'heading': heading}
        last, lead = None, None
        for line in lines[start+1:stop]:
            field = re.match(r'^(\s*)([a-z][a-z-]*):\s*(.*)', line)
            if field:
                indent, key, val = field.groups()
                if key == 'lead':
                    lead = {'lead': val}
                    entry.setdefault('leads', []).append(lead)
                    last = (lead, 'lead')
                else:
                    target = lead if indent and lead is not None else entry
                    if key in target:
                        raise ValueError('duplicate ledger field '+key)
                    target[key] = val
                    last = (target, key)
            elif line.strip() and last:
                target, key = last
                target[key] += ' '+line.strip()
        entries.append(entry)
    return header, entries


def unquote(value):
    value = value.strip()
    try:
        obj, _ = json.JSONDecoder().raw_decode(value)
        if isinstance(obj, str):
            return obj
    except ValueError:
        pass
    m = re.match(r'^[“\"](.*?)[”\"](?:\s|$)', value)
    return m[1] if m else value


def grade_shared(root, contract, before, events=()):
    """Return three separately visible gates; fail closed on missing evidence.

    Contract: protected files are all original files except declared ledger/companion;
    sources map identities to independently pinned bytes; items map expected claims
    to sources. Applicability is explicit (bib archives are exempt).
    """
    root = Path(root)
    checks = {'archive': [], 'ledger': [], 'preservation': []}
    def add(group, name, passed, detail=''):
        checks[group].append({'check': name, 'passed': bool(passed), 'detail': detail})
    after = snapshot(root)
    ledger_rel = contract.get('ledger', 'literature/verifications.md')
    companion_rel = contract.get('companion')
    protected = set(before) - {ledger_rel, companion_rel}
    for rel in sorted(protected):
        add('preservation', rel, before[rel] == after.get(rel), 'original file bytes/type/mode unchanged')
    allowed_new = contract.get('allowed_new_prefixes', ['literature/'])
    for rel in sorted(set(after)-set(before)):
        add('preservation', 'new-file:'+rel,
            any(rel.startswith(p) for p in allowed_new) and after[rel]['kind'] == 'file',
            'new files restricted to declared literature output paths; no symlinks')
    # Tool harness denies transient protected writes. External before/after-only
    # callers cannot make that stronger claim.
    attempts = [e for e in events if e.get('operation') in {'write_file','copy_file'} and e.get('denied')]
    for e in attempts:
        add('preservation', 'denied-write:'+e.get('path','?'), False, 'attempted forbidden write')
    try:
        lp = safe_path(root, ledger_rel)
        ledger = lp.read_text(encoding='utf-8')
        header, entries = parse_ledger(ledger)
    except (OSError, ValueError) as error:
        add('ledger', 'readable-ledger', False, str(error))
        header, entries, ledger = {}, [], ''
    else:
        add('ledger', 'readable-ledger', True)
    prefix = contract.get('ledger_prefix', '')
    add('ledger', 'append-only-history', ledger.startswith(prefix), 'pre-existing Markdown must be an exact prefix')
    add('ledger', 'declared-store', header.get('store') == contract.get('store', 'literature/sources/'))
    add('ledger', 'maintainer-recorded', bool(header.get('maintained-by')))
    if companion_rel:
        add('ledger', 'companion-declaration', header.get('companion') == companion_rel)
    elif header.get('companion'):
        add('ledger', 'unexpected-companion', False, 'benchmark did not authorize enabling a companion')
    try:
        _, old_entries = parse_ledger(prefix)
    except ValueError:
        old_entries = []
    fresh_entries = entries[len(old_entries):]
    for entry in fresh_entries:
        try:
            ts = datetime.fromisoformat(entry['ts'].replace('Z','+00:00'))
            valid = ts.utcoffset() is not None and ts.utcoffset().total_seconds() == 0
            if contract.get('started_at'):
                valid &= ts >= datetime.fromisoformat(contract['started_at'].replace('Z','+00:00')).replace(second=0,microsecond=0)
            if contract.get('finished_at'):
                valid &= ts <= datetime.fromisoformat(contract['finished_at'].replace('Z','+00:00'))
        except (ValueError, KeyError):
            valid = False
        add('ledger', 'timestamp:'+entry.get('heading','?'), valid, 'parseable UTC verification timestamp within run')
    relevant = [e for e in fresh_entries if e.get('type') == contract.get('entry_type','cite')]
    add('ledger', 'entry-count', len(relevant) == len(contract.get('items', [])),
        'fresh entry count equals scoped claim–source pairs')
    for item in contract.get('items', []):
        matches = [e for e in relevant if ' '.join(unquote(e.get('claim','')).split()) == ' '.join(item['claim'].split())
                   and source_matches(e.get('source',''),item['source'])]
        add('ledger', 'coverage:'+item['id'], len(matches) == 1, 'one fresh entry per expected claim–source pair')
        for entry in matches:
            fields = ['claim','claim-hash','source','version-read','archived','license','verdict','evidence']
            add('ledger', 'fields:'+item['id'], all(entry.get(k,'').strip() for k in fields))
            add('ledger', 'claim-hash:'+item['id'], entry.get('claim-hash') == claim_hash(item['claim']))
            add('ledger', 'verdict:'+item['id'], entry.get('verdict') in {'supported','partially supported','unsupported','unverifiable'})
            if item.get('reported_verdict'):
                add('ledger', 'reported-verdict-agreement:'+item['id'],entry.get('verdict')==item['reported_verdict'])
            add('ledger', 'location:'+item['id'],
                bool(re.search(r' — '+re.escape(item.get('file','manuscript.md'))+':'+
                               (str(item['line']) if 'line' in item else r'\d+')+'$',entry['heading'])))
            if item['source'].startswith('doi:'):
                add('ledger', 'updates:'+item['id'], bool(entry.get('updates')),
                    'field presence only; no claim of independently verifying registrar queries')
            if entry.get('verdict') != 'unverifiable':
                add('ledger', 'evidence:'+item['id'],
                    entry.get('evidence','').lower().strip() not in {'','none','n/a'} and
                    bool(re.search(r'\([^)]*(?:p\d|sec|paragraph|line)[^)]*\)',entry.get('evidence',''),re.I)),
                    'evidence and locator recorded; quotation fidelity/meaning graded separately')
    archive_required = contract.get('archive_required', True)
    if archive_required:
        records = relevant
        for source in contract.get('sources', []):
            matching = [e for e in records if source_matches(e.get('source',''),source['identity'])]
            observed = any(e.get('operation') == 'read_file' and e.get('path') == source['input']
                           and e.get('sha256') == source['sha256'] and not e.get('denied') for e in events)
            add('archive','independently-observed-read:'+source['identity'],observed,
                'evaluator-owned read trace, not the agent’s own hash assertion')
            add('archive','source-covered:'+source['identity'],bool(matching))
            for entry in matching:
                m = re.fullmatch(r'(.+?)\s+sha256:([0-9a-fA-F]{64})',entry.get('archived',''))
                ok, detail = False, 'missing or malformed archived path/hash'
                if m:
                    rel, recorded = m.groups()
                    try:
                        ap = safe_path(root,rel)
                        actual = sha(ap.read_bytes())
                        # Same bytes as independent, retrieved source snapshot: a
                        # fabricated quotes-only archive cannot satisfy this gate.
                        ok = (actual == recorded.lower() == source['sha256'] and
                              rel.startswith(contract.get('store','literature/sources/')) and
                              rel != source['input'])
                        identity = source['identity'].removeprefix('doi:')
                        id8 = sha(identity.encode())[:8]
                        ok &= bool(re.search(r'-'+id8+r'(?:--[^/]*)?\.[a-z0-9]+$',rel))
                        detail = rel
                    except (OSError,ValueError) as error:
                        detail = str(error)
                add('archive','archive:'+entry.get('heading','?'),ok,detail)
                add('archive','license:'+entry.get('heading','?'),
                    bool(entry.get('license')) and entry.get('license') != 'n/a')
                if source.get('license'):
                    canonical=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
                    add('archive','pinned-license:'+entry.get('heading','?'),
                        canonical(source['license']) in canonical(entry.get('license','')) or
                        bool(source.get('license_url') and source['license_url'].lower() in entry.get('license','').lower()))
    else:
        add('archive','not-applicable',True,contract.get('archive_exemption','metadata-only audit; no source text read'))
    if companion_rel:
        try:
            cp = safe_path(root,companion_rel)
            rows = [json.loads(line) for line in cp.read_text().splitlines() if line.strip()]
            add('ledger','jsonl-mirrors-markdown', rows == entries)
        except (OSError,ValueError) as error:
            add('ledger','jsonl-mirrors-markdown',False,str(error))
    groups = {name: {'passed': bool(rows) and all(r['passed'] for r in rows), 'checks': rows}
              for name, rows in checks.items()}
    return {'schema':'citation-needed.shared-checks/2', 'groups':groups,
            'passed': all(g['passed'] for g in groups.values()),
            'limitations': ['Local pinned-source contract, not a cloud archive verifier.',
                            'Does not determine claim support, source licensing truth, or live registrar/reuse freshness.',
                            'Transient edits are prevented/logged only when used with the restricted API tool harness.']}


if __name__ == '__main__':
    import argparse
    import sys
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    snap=sub.add_parser('snapshot')
    snap.add_argument('--workspace',type=Path,required=True)
    snap.add_argument('--output',type=Path,required=True)
    grade=sub.add_parser('grade')
    grade.add_argument('--workspace',type=Path,required=True)
    grade.add_argument('--contract',type=Path,required=True)
    grade.add_argument('--before',type=Path,required=True)
    grade.add_argument('--events',type=Path,required=True)
    grade.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.resolve().is_relative_to(args.workspace.resolve()):
        parser.error('evaluator snapshots and grades must stay outside the agent workspace')
    if args.command=='snapshot':
        result=snapshot(args.workspace)
    else:
        result=grade_shared(args.workspace,json.loads(args.contract.read_text()),
            json.loads(args.before.read_text()),json.loads(args.events.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Snapshot saved.' if args.command=='snapshot' else ('PASS' if result['passed'] else 'FAIL'))
    sys.exit(0 if args.command=='snapshot' or result['passed'] else 1)
