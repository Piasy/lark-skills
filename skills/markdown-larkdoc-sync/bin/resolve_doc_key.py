from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from doc_binding import resolve_declared_doc, to_payload
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('declared_doc')
    args = parser.parse_args()

    dump_json(to_payload(resolve_declared_doc(args.declared_doc)), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
