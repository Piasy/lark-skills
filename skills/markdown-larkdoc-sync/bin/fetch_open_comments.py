from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from comments import flatten_open_comments
from jsonio import dump_json
from lark_cli import LarkCLI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_token')
    parser.add_argument('file_type')
    args = parser.parse_args()

    raw = LarkCLI().run_json(
        [
            'drive',
            'file.comments',
            'list',
            '--params',
            json.dumps({'file_token': args.file_token, 'file_type': args.file_type}, ensure_ascii=False),
        ]
    )
    dump_json({'items': flatten_open_comments(raw)}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
