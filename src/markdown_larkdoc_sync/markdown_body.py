from __future__ import annotations

from datetime import date, datetime, time
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised via fallback behavior
    yaml = None


_FRONTMATTER_PATTERN = re.compile(
    r'^---(?:\r?\n)(.*?)(?:\r?\n)---(?:\r?\n|$)',
    flags=re.DOTALL,
)
_OPENING_FENCE_PATTERN = re.compile(r'^[ ]{0,3}(?P<fence>(?:`{3,}|~{3,})).*$')
_CLOSING_FENCE_PATTERN = re.compile(r'^[ ]{0,3}(?P<fence>(?:`{3,}|~{3,}))[ \t]*$')


def _normalize_frontmatter_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, dict):
        return {
            _normalize_frontmatter_value(key): _normalize_frontmatter_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_normalize_frontmatter_value(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_frontmatter_value(item) for item in value]
    if isinstance(value, set):
        return [_normalize_frontmatter_value(item) for item in value]
    return value


def _parse_scalar(value: str) -> Any:
    if value in {'null', 'Null', 'NULL', '~'}:
        return None
    if value == 'true':
        return True
    if value == 'false':
        return False
    if value.startswith(('"', "'")) and value.endswith(('"', "'")) and len(value) >= 2:
        return value[1:-1]
    return value


def _parse_simple_yaml_mapping(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue

        indent = len(raw_line) - len(raw_line.lstrip(' '))
        stripped = raw_line.strip()
        key, sep, value = stripped.partition(':')
        if not sep:
            raise ValueError(f'Invalid frontmatter line: {raw_line!r}')

        while indent <= stack[-1][0]:
            stack.pop()

        current = stack[-1][1]
        cleaned_key = key.strip()
        cleaned_value = value.lstrip()
        if cleaned_value:
            current[cleaned_key] = _parse_scalar(cleaned_value)
            continue

        child: dict[str, Any] = {}
        current[cleaned_key] = child
        stack.append((indent, child))

    return root


def _load_frontmatter(frontmatter_text: str) -> dict[str, Any]:
    # PyYAML is the primary parser. Keep a lightweight fallback only for
    # environments where the runtime dependency is unexpectedly unavailable.
    if yaml is not None:
        data = yaml.safe_load(frontmatter_text) or {}
        if not isinstance(data, dict):
            raise ValueError('Frontmatter must decode to a mapping')
        normalized = _normalize_frontmatter_value(data)
        if not isinstance(normalized, dict):
            raise ValueError('Frontmatter must decode to a mapping')
        return normalized
    return _parse_simple_yaml_mapping(frontmatter_text)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    match = _FRONTMATTER_PATTERN.match(text)
    if match is None:
        return {}, text

    frontmatter_text = match.group(1)
    body = text[match.end() :]
    return _load_frontmatter(frontmatter_text), body.lstrip('\r\n')


def normalize_body(body: str) -> str:
    normalized: list[str] = []
    in_fence = False
    fence_char = ''
    fence_length = 0

    for line in body.splitlines():
        if in_fence:
            closing_match = _CLOSING_FENCE_PATTERN.match(line)
            if (
                closing_match
                and closing_match.group('fence').startswith(fence_char)
                and len(closing_match.group('fence')) >= fence_length
            ):
                in_fence = False
                fence_char = ''
                fence_length = 0
            normalized.append(line)
            continue

        opening_match = _OPENING_FENCE_PATTERN.match(line)
        if opening_match:
            fence = opening_match.group('fence')
            in_fence = True
            fence_char = fence[0]
            fence_length = len(fence)
            normalized.append(line)
            continue
        normalized.append(line if in_fence else line.rstrip())

    return '\n'.join(normalized).rstrip() + '\n'


def read_markdown_parts(path: Path) -> tuple[dict[str, Any], str]:
    return split_frontmatter(path.read_text(encoding='utf-8'))
