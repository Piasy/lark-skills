from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from doc_binding import resolve_declared_doc
from frontmatter import split_frontmatter
from jsonio import dump_json
from lark_cli import LarkCLI
from mermaid_addons import (
    canonicalize_markdown,
    contains_whiteboard,
    extract_remote_markdown,
    replace_mermaid_fences_with_placeholders,
    replace_placeholder_blocks_with_addons,
)


def _prepare_temp_markdown(transport_body: str) -> tuple[Path, Path]:
    # lark-cli --markdown @file requires the file to be within working directory.
    temp_root = Path(tempfile.mkdtemp(prefix='markdown-larkdoc-sync-'))
    markdown_path = temp_root / 'write-back.md'
    markdown_path.write_text(transport_body, encoding='utf-8')
    return temp_root, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('declared_doc')
    parser.add_argument('identity')
    args = parser.parse_args()

    markdown_path = Path(args.markdown_path)
    text = markdown_path.read_text(encoding='utf-8')
    _, body = split_frontmatter(text)

    transport_body, mermaid_blocks = replace_mermaid_fences_with_placeholders(body)

    temp_root: Path | None = None
    try:
        temp_root, _ = _prepare_temp_markdown(transport_body)

        lark = LarkCLI()
        resolved = resolve_declared_doc(args.declared_doc, lark_cli=lark)
        if resolved.resolved_file_type != 'docx':
            raise RuntimeError(f'unsupported resolved file type for docx APIs: {resolved.resolved_file_type}')

        document_id = resolved.resolved_doc_token
        update_result = lark.run_json(
            [
                'docs',
                '+update',
                '--doc',
                document_id,
                '--as',
                args.identity,
                '--mode',
                'overwrite',
                '--markdown',
                '@./write-back.md',
            ],
            cwd=temp_root,
        )

        replacements = replace_placeholder_blocks_with_addons(
            lark,
            document_id=document_id,
            identity=args.identity,
            blocks=mermaid_blocks,
        )

        fetch_result = lark.run_json(
            [
                'docs',
                '+fetch',
                '--doc',
                document_id,
                '--as',
                args.identity,
                '--format',
                'json',
            ]
        )
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)

    remote_body_raw = extract_remote_markdown(fetch_result)
    remote_raw_text = remote_body_raw if isinstance(remote_body_raw, str) else ''
    remote_canonical, remote_addons_converted = canonicalize_markdown(remote_raw_text)
    local_canonical, _ = canonicalize_markdown(body)

    verified = isinstance(remote_body_raw, str) and remote_canonical == local_canonical

    payload: dict[str, object] = {
        'markdown_path': args.markdown_path,
        'declared_doc': args.declared_doc,
        'identity': args.identity,
        'resolved_doc_token': resolved.resolved_doc_token,
        'resolved_file_type': resolved.resolved_file_type,
        'mode': 'overwrite',
        'local_body_length': len(body),
        'remote_body_length': len(remote_raw_text) if isinstance(remote_body_raw, str) else None,
        'mermaid_block_count': len(mermaid_blocks),
        'remote_addons_converted': remote_addons_converted,
        'remote_contains_whiteboard': contains_whiteboard(remote_raw_text),
        'addon_replacements': replacements,
        'verified': verified,
        'update_result': update_result,
    }
    if not verified:
        payload['reason'] = 'remote canonical body differs from local canonical body after overwrite/add-on write-back'

    dump_json(payload, sys.stdout)
    return 0 if verified else 2


if __name__ == '__main__':
    raise SystemExit(main())
