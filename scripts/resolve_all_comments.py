from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from markdown_larkdoc_sync.comments import build_resolve_payload, collect_open_comment_ids, dump_json_arg
from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.lark_cli import LarkCLI


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_token')
    parser.add_argument('file_type')
    args = parser.parse_args()

    lark = LarkCLI()
    raw = lark.run_json(
        [
            'drive',
            'file.comments',
            'list',
            '--params',
            json.dumps({'file_token': args.file_token, 'file_type': args.file_type}, ensure_ascii=False),
        ]
    )
    comment_ids = collect_open_comment_ids(raw)

    results = []
    for comment_id in comment_ids:
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

    dump_json({'resolved_comment_ids': comment_ids, 'results': results}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
