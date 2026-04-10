from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from markdown_larkdoc_sync.doc_binding import resolve_declared_doc, to_payload
from markdown_larkdoc_sync.jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('declared_doc')
    args = parser.parse_args()

    dump_json(to_payload(resolve_declared_doc(args.declared_doc)), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
