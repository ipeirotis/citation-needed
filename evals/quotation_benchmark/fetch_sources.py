"""Retrieve the pinned public JATS sources for reproduction; no credentials."""
import argparse
import json
import time
import urllib.request
from pathlib import Path
from .build_dataset import DATA, digest


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache',type=Path,required=True)
    args=ap.parse_args()
    args.cache.mkdir(parents=True,exist_ok=True)
    cases=json.loads((DATA/'manifest.json').read_text())['cases']
    for case in cases:
        target=args.cache/(case['pmcid']+'.xml')
        if target.exists():
            data=target.read_bytes()
        else:
            with urllib.request.urlopen(case['retrieval_url'],timeout=60) as response:
                data=response.read()
            time.sleep(.5)
        if digest(data)!=case['xml_sha256']:
            raise ValueError('Pinned XML differs: '+case['pmcid']+'; do not silently regenerate labels')
        target.write_bytes(data)
        print(case['pmcid'],'verified')
    # Metadata projection sufficient for the builder; order is the frozen case order.
    records=[{'pmcid':c['pmcid'],'doi':c['doi'],'authorString':c['authors'],'pubYear':c['year']} for c in cases]
    (args.cache/'candidates.json').write_text(json.dumps({'resultList':{'result':records}},indent=2)+'\n')


if __name__=='__main__':
    main()
