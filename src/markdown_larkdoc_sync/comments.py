from __future__ import annotations

import json
from typing import Any


def flatten_open_comments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get('items', [])
    return [item for item in items if not item.get('is_solved', False)]


def build_resolve_payload(file_token: str, file_type: str, comment_id: str) -> dict[str, dict[str, Any]]:
    return {
        'params': {'file_token': file_token},
        'data': {'file_type': file_type, 'comment_id': comment_id, 'is_solved': True},
    }


def dump_json_arg(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
