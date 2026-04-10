from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from markdown_larkdoc_sync.git_sync import find_last_sync_commit
from markdown_larkdoc_sync.jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('doc_key')
    args = parser.parse_args()

    dump_json(find_last_sync_commit(Path.cwd(), args.doc_key, args.markdown_path), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
