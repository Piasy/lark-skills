from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from frontmatter import split_frontmatter
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    args = parser.parse_args()

    text = Path(args.markdown_path).read_text(encoding='utf-8')
    frontmatter, body = split_frontmatter(text)
    dump_json({'frontmatter': frontmatter, 'body': body}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
