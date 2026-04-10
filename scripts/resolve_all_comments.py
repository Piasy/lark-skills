from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from markdown_larkdoc_sync.comments import build_resolve_payload, dump_json_arg
from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.lark_cli import LarkCLI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_token')
    parser.add_argument('file_type')
    parser.add_argument('comment_ids', nargs='+')
    args = parser.parse_args()

    lark = LarkCLI()
    results = []
    for comment_id in args.comment_ids:
        payload = build_resolve_payload(args.file_token, args.file_type, comment_id)
        results.append(
            lark.run_json(
                [
                    'drive',
                    'file.comments',
                    'patch',
                    '--params',
                    dump_json_arg(payload['params']),
                    '--data',
                    dump_json_arg(payload['data']),
                ]
            )
        )

    dump_json({'results': results}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
