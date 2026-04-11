from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from frontmatter import split_frontmatter, write_frontmatter_to_text
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('--doc', required=True)
    parser.add_argument('--as', dest='identity', required=True)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--title')
    args = parser.parse_args()

    markdown_path = Path(args.markdown_path)
    text = markdown_path.read_text(encoding='utf-8') if markdown_path.exists() else ''
    _, body = split_frontmatter(text)

    content = write_frontmatter_to_text(
        body=body,
        title=args.title,
        doc=args.doc,
        identity=args.identity,
        profile=args.profile,
    )
    markdown_path.write_text(content, encoding='utf-8')

    dump_json(
        {
            'markdown_path': args.markdown_path,
            'frontmatter_written': {
                'title': args.title,
                'markdown_larkdoc_sync': {
                    'doc': args.doc,
                    'as': args.identity,
                    'profile': args.profile,
                },
            },
        },
        sys.stdout,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
