from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

from markdown_larkdoc_sync.lark_cli import LarkCLI


@dataclass(frozen=True)
class ResolvedDoc:
    declared_doc: str
    resolved_doc_token: str
    resolved_file_type: str
    doc_key: str


def _extract_kind_and_token(declared_doc: str) -> tuple[str, str]:
    if declared_doc.startswith('//'):
        raise ValueError(f'unsupported declared doc: {declared_doc}')

    if '://' not in declared_doc:
        if '/' in declared_doc:
            raise ValueError(f'unsupported declared doc: {declared_doc}')
        return 'docx', declared_doc

    parsed = urlparse(declared_doc)
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) >= 2 and parts[0] in {'docx', 'doc', 'wiki'}:
        return parts[0], parts[1]

    raise ValueError(f'unsupported declared doc: {declared_doc}')


def resolve_declared_doc(declared_doc: str, lark_cli: LarkCLI | None = None) -> ResolvedDoc:
    cli = lark_cli or LarkCLI()
    kind, token = _extract_kind_and_token(declared_doc)

    if kind == 'wiki':
        node = cli.run_json(['wiki', 'spaces', 'get_node', '--params', json.dumps({'token': token})])['node']
        kind = node['obj_type']
        token = node['obj_token']

    return ResolvedDoc(
        declared_doc=declared_doc,
        resolved_doc_token=token,
        resolved_file_type=kind,
        doc_key=f'{kind}:{token}',
    )


def to_payload(resolved: ResolvedDoc) -> dict[str, str]:
    return asdict(resolved)
