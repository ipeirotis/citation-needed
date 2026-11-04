#!/usr/bin/env python3
"""Build paper-derived quotation manuscripts from pinned, licensed JATS XML.

Network retrieval is an explicit separate step. No LLM or checker supplies labels.
"""
import argparse
import hashlib
import json
import re
import random
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'evals/quotation-dataset'
XLINK = '{http://www.w3.org/1999/xlink}href'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def text(node):
    return ' '.join(''.join(node.itertext()).split()) if node is not None else ''


def paragraphs(root):
    """Abstract and body prose only; exclude tables, captions, refs, peer review."""
    out = []
    def walk(node, section):
        if node.tag in {'table-wrap', 'fig', 'supplementary-material', 'boxed-text'}:
            return
        if node.tag == 'sec':
            section = text(node.find('title')) or section
        if node.tag == 'p':
            value = text(node)
            if value:
                out.append({'id': f'p{len(out)+1:04d}', 'section': section, 'text': value})
            return
        for child in node:
            walk(child, section)
    abstract = root.find('./front/article-meta/abstract')
    if abstract is not None:
        walk(abstract, 'Abstract')
    body = root.find('body')
    if body is not None:
        walk(body, 'Body')
    return out


def sentences(paras):
    out = []
    for p in paras:
        for s in re.split(r'(?<=[.!?])\s+(?=[A-Z(])', p['text']):
            s = s.strip()
            # Avoid fragments from decimal splitting, bracketed citations and nested quotes.
            if (12 <= len(s.split()) <= 65 and s[0].isupper() and s.endswith(('.', '!', '?'))
                    and not re.search(r'\b(?:[A-Z]|al|e\.g|i\.e|Fig|spp)\.$',s)
                    and not any(c in s for c in ['“', '”', '"', '\n'])):
                out.append((p, s))
    return out


def make_items(paras, seed=0):
    pool = sentences(paras)
    used = set()
    def choose(predicate):
        for p, s in pool:
            if p['id'] not in used and predicate(s):
                used.add(p['id'])
                return p, s
        raise ValueError('not enough suitable independent passages')
    variants = []
    p, s = choose(lambda s: not re.search(r'\bnot\b', s))
    variants.append(('accurate', p, s, s, 'valid', 'Unchanged complete sentence.'))
    p, s = choose(lambda s: ' ' in s and not re.search(r'\bnot\b', s))
    words = s.split(' ')
    # Whitespace normalization is intentionally in the prototype contract.
    if seed % 3 == 0:
        q = '\n'.join([' '.join(words[:len(words)//2]), ' '.join(words[len(words)//2:])])
        why = 'Line wrap only; no word, number or punctuation changes.'
    elif seed % 3 == 1:
        q = s.replace(' ', '\u00a0')
        why = 'Nonbreaking spaces replace ordinary spaces; wording and numbers unchanged.'
    else:
        q = s.replace(' ', '  ')
        why = 'Repeated spaces only; wording and numbers unchanged.'
    variants.append(('formatting', p, s, q, 'valid', why))
    swaps = [('were', 'are'), ('was', 'is'), ('is', 'was'), ('are', 'were'),
             ('study', 'investigation'), ('data', 'observations'), ('results', 'findings')]
    p, s = choose(lambda s: any(re.search(r'\b'+a+r'\b', s) for a, _ in swaps))
    for a, b in swaps:
        if re.search(r'\b'+a+r'\b', s):
            q = re.sub(r'\b'+a+r'\b', b, s, count=1)
            why = f'Direct quotation changes {a!r} to {b!r}; even a plausible paraphrase is not verbatim.'
            break
    variants.append(('altered_wording', p, s, q, 'invalid', why))
    def number(s):
        # Reference indices, identifiers, list numbers and figure numbers are
        # not the intended quantitative-quotation targets.
        masked = re.sub(r'\[[^]]*\]',lambda m:' '*len(m[0]),s)
        masked = re.sub(r'\b(?:Fig(?:ure)?|Table|section)\s+\d+',lambda m:' '*len(m[0]),masked,flags=re.I)
        for m in re.finditer(r'(?<![\w.])\d+(?:\.\d+)?(?![\w.])',masked):
            before = s[m.start()-1:m.start()] if m.start() else ''
            after = s[m.end():m.end()+1]
            if before not in {'-', '('} and after not in {'-', ')'}:
                return m
        return None
    p, s = choose(lambda s: number(s) is not None)
    m = number(s)
    old = m.group()
    new = str(int(old)+1) if '.' not in old else str(int(old.split('.')[0])+1)+'.'+old.split('.')[1]
    q = s[:m.start()] + new + s[m.end():]
    variants.append(('altered_number', p, s, q, 'invalid', f'Quoted numeral changed from {old} to {new}.'))
    p, s = choose(lambda s: re.search(r'\b(?:did|does|do|was|were|is|are|have|has|had|could|can|would|should|will|may) not\b(?! (?:only|just)\b)', s) is not None)
    negation = re.search(r'\b(?:did|does|do|was|were|is|are|have|has|had|could|can|would|should|will|may) (not(?: yet)?)(?! (?:only|just)\b)',s)
    q = s[:negation.start(1)]+'…'+s[negation.end(1):]
    variants.append(('misleading_omission', p, s, q, 'invalid',
                     'Ellipsis removes an explicit negation; surviving words alone do not preserve the assertion.'))
    p, s = choose(lambda s: not re.search(r'\b(?:not|however|although|but|unless|except|despite)\b', s, re.I)
                  and re.search(r'\b(?:used|performed|collected|conducted|measured|included)\b',s,re.I) is not None)
    variants.append(('benign_omission', p, s, s+' …', 'valid',
                     'Complete sentence retained; trailing ellipsis indicates later text is not quoted, without deleting any words from this sentence.'))
    random.Random(seed).shuffle(variants)
    out = []
    for i, (kind, p, s, q, verdict, why) in enumerate(variants, 1):
        status = {'accurate': 'exact', 'formatting': 'normalized',
                  'altered_wording': 'not_found', 'altered_number': 'not_found',
                  'misleading_omission': 'manual_review', 'benign_omission': 'manual_review'}[kind]
        if kind in {'altered_wording','altered_number'} and re.search(r'\[[^]]*\]|\.{3}|…',q):
            status = 'manual_review'
        out.append({'id': f'Q{i}', 'kind': kind, 'paragraph_id': p['id'], 'section': p['section'],
                    'original': s, 'quote': q, 'expected': verdict, 'reason': why,
                    'context': p['text'], 'expected_checker_status': status})
    return out


def build(cache, candidates, count=30):
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA/'sources').mkdir(exist_ok=True)
    (DATA/'manuscripts').mkdir(exist_ok=True)
    manifest, keys, rejected = [], {}, []
    records = json.loads(candidates.read_text())['resultList']['result']
    for record in records:
        pmc = record.get('pmcid', '')
        path = cache/(pmc+'.xml')
        if not path.exists():
            continue
        raw = path.read_bytes()
        root = ET.fromstring(raw)
        licenses = root.findall('./front/article-meta/permissions/license')
        license_urls = [n.get(XLINK, '') for lic in licenses for n in lic.iter()]
        license_url = next((u for u in license_urls if re.fullmatch(r'https?://creativecommons.org/licenses/by/(?:3\.0|4\.0)/?', u)), None)
        if not license_url or root.get('article-type') != 'research-article':
            rejected.append({'pmcid': pmc, 'reason': 'license/type'})
            continue
        paras = paragraphs(root)
        try:
            items = make_items(paras, seed=len(manifest)+1)
        except ValueError as e:
            rejected.append({'pmcid': pmc, 'reason': str(e)})
            continue
        doi = text(root.find('./front/article-meta/article-id[@pub-id-type="doi"]'))
        if doi != record.get('doi'):
            raise ValueError('metadata/XML DOI disagreement '+pmc)
        case = f'M{len(manifest)+1:02d}'
        title = text(root.find('./front/article-meta/title-group/article-title'))
        source = f'# {title}\n\nDOI: https://doi.org/{doi}\nPMCID: {pmc}\nAuthors: {record["authorString"]}\nLicense: {license_url}\n\n'
        source += '\n\n'.join(f'## {p["id"]} — {p["section"]}\n\n{p["text"]}' for p in paras)+'\n'
        source_bytes = source.encode()
        (DATA/'sources'/f'{case}.txt').write_bytes(source_bytes)
        by_para = {x['paragraph_id']: x for x in items}
        manuscript = f'# EVALUATION COPY — {title}\n\n'
        manuscript += ('This is an altered, plain-text research-article adaptation for quotation testing. '
                       'The original authors did not write or endorse the inserted quotations. '
                       'Body and abstract prose are retained; tables, figures, references and peer-review attachments are excluded. '
                       'Only labelled quotation blocks Q1–Q6 are in scope.\n\n')
        manuscript += f'Original authors: {record["authorString"]}\nOriginal paper: https://doi.org/{doi}\nLicense: {license_url}\n\n'
        for p in paras:
            value = p['text']
            item = by_para.get(p['id'])
            if item:
                marker = f'[{item["id"]}] The source states: “{item["quote"]}” [@source].'
                value = value.replace(item['original'], marker, 1)
                item['claim'] = marker
                item['claim_hash'] = digest(' '.join(marker.split()).encode())[:12]
            manuscript += f'## {p["id"]} — {p["section"]}\n\n{value}\n\n'
        manuscript += f'## Source for labelled quotations\n\n[@source]: {record["authorString"]} ({record["pubYear"]}). {title} https://doi.org/{doi}\n'
        (DATA/'manuscripts'/f'{case}.md').write_text(manuscript, encoding='utf-8')
        for item in items:
            item['line'] = next(i for i, line in enumerate(manuscript.splitlines(), 1) if f'[{item["id"]}] The source states:' in line)
            item['review_status'] = 'pending contextual review'
        manifest.append({'id': case, 'doi': doi, 'pmcid': pmc, 'title': title,
                         'authors': record['authorString'], 'year': record['pubYear'],
                         'license_url': license_url, 'license_statement': ' '.join(text(x) for x in licenses),
                         'retrieved': '2026-11-04', 'retrieval_url': f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML',
                         'xml_sha256': digest(raw), 'source': f'sources/{case}.txt',
                         'source_sha256': digest(source_bytes), 'manuscript': f'manuscripts/{case}.md',
                         'manuscript_sha256': digest(manuscript.encode()), 'paragraph_count': len(paras),
                         'word_count': len(manuscript.split()), 'items': len(items)})
        keys[case] = items
        if len(manifest) == count:
            break
    if len(manifest) != count:
        raise ValueError(f'only {len(manifest)} usable sources; need {count}; rejected {rejected}')
    (DATA/'manifest.json').write_text(json.dumps({'schema': 'quotation-dataset/1', 'cases': manifest, 'rejected': rejected}, ensure_ascii=False, indent=2)+'\n')
    (DATA/'answer-key.json').write_text(json.dumps(keys, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'manuscripts': len(manifest), 'items': sum(x['items'] for x in manifest), 'rejected': rejected}, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path, required=True)
    ap.add_argument('--candidates', type=Path, required=True)
    args = ap.parse_args()
    build(args.cache, args.candidates)
