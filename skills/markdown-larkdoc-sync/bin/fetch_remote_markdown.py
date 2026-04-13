from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from doc_binding import resolve_declared_doc
from jsonio import dump_json
from lark_cli import LarkCLI
from mermaid_addons import canonicalize_markdown, contains_whiteboard, extract_remote_markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('declared_doc')
    parser.add_argument('identity')
    parser.add_argument('--canonical', action='store_true')
    args = parser.parse_args()

    lark = LarkCLI()
    resolved = resolve_declared_doc(args.declared_doc, lark_cli=lark)
    if resolved.resolved_file_type != 'docx':
        raise RuntimeError(f'unsupported resolved file type for fetch: {resolved.resolved_file_type}')

    fetch_result = lark.run_json(
        [
            'docs',
            '+fetch',
            '--doc',
            resolved.resolved_doc_token,
            '--as',
            args.identity,
            '--format',
            'json',
        ]
    )

    raw_markdown = extract_remote_markdown(fetch_result) or ''
    canonical_markdown, converted = canonicalize_markdown(raw_markdown)

    payload: dict[str, object] = {
        'declared_doc': args.declared_doc,
        'identity': args.identity,
        'resolved_doc_token': resolved.resolved_doc_token,
        'resolved_file_type': resolved.resolved_file_type,
        'raw_markdown': raw_markdown,
        'raw_length': len(raw_markdown),
        'contains_whiteboard': contains_whiteboard(raw_markdown),
        'addon_mermaid_converted': converted,
    }
    if args.canonical:
        payload['markdown'] = canonical_markdown
        payload['length'] = len(canonical_markdown)
    else:
        payload['markdown'] = raw_markdown
        payload['length'] = len(raw_markdown)

    dump_json(payload, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
