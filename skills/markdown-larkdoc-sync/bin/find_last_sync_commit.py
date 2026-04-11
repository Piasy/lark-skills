from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from git_sync import find_last_sync_commit
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('doc_key')
    args = parser.parse_args()

    dump_json(find_last_sync_commit(Path.cwd(), args.doc_key, args.markdown_path), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
