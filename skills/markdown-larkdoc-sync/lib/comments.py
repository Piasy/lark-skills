from __future__ import annotations

import json
from typing import Any


def flatten_open_comments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get('items')
    if items is None and isinstance(payload.get('data'), dict):
        items = payload['data'].get('items', [])
    if items is None:
        items = []
    return [item for item in items if not item.get('is_solved', False)]


def collect_open_comment_ids(payload: dict[str, Any]) -> list[str]:
    return [item['comment_id'] for item in flatten_open_comments(payload) if item.get('comment_id')]


def build_resolve_payload(file_token: str, file_type: str, comment_id: str) -> dict[str, dict[str, Any]]:
    return {
        'params': {'file_token': file_token, 'comment_id': comment_id, 'file_type': file_type},
        'data': {'is_solved': True},
    }


def dump_json_arg(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
