from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from markdown_larkdoc_sync.jsonio import dump_json
from markdown_larkdoc_sync.markdown_body import normalize_body, read_markdown_parts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    args = parser.parse_args()

    frontmatter, body = read_markdown_parts(Path(args.markdown_path))
    dump_json({'frontmatter': frontmatter, 'body': normalize_body(body)}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
