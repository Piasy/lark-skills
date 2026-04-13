from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from typing import Any

from lark_cli import LarkCLI

MERMAID_COMPONENT_TYPE_ID = 'blk_631fefbbae02400430b8f9f4'
MERMAID_VIEW = 'codeChart'


@dataclass(frozen=True)
class MermaidBlock:
    placeholder: str
    code: str


def extract_remote_markdown(payload: dict[str, object]) -> str | None:
    data = payload.get('data')
    if isinstance(data, dict):
        markdown = data.get('markdown')
        if isinstance(markdown, str):
            return markdown

    markdown = payload.get('markdown')
    if isinstance(markdown, str):
        return markdown

    return None


def contains_whiteboard(markdown: str) -> bool:
    return '<whiteboard ' in markdown


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith('\r\n'):
        return line[:-2], '\r\n'
    if line.endswith('\n'):
        return line[:-1], '\n'
    return line, ''


def replace_mermaid_fences_with_placeholders(markdown: str) -> tuple[str, list[MermaidBlock]]:
    lines = markdown.splitlines(keepends=True)
    marker = hashlib.sha1(markdown.encode('utf-8')).hexdigest()[:8]

    output: list[str] = []
    blocks: list[MermaidBlock] = []

    i = 0
    while i < len(lines):
        current_text, current_eol = _split_line_ending(lines[i])
        start_match = re.match(r'^([ \t]*)```mermaid[ \t]*$', current_text)
        if start_match is None:
            output.append(lines[i])
            i += 1
            continue

        code_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            candidate_text, _ = _split_line_ending(lines[j])
            if re.match(r'^[ \t]*```[ \t]*$', candidate_text):
                break
            code_lines.append(lines[j])
            j += 1

        if j >= len(lines):
            # Unclosed mermaid fence: keep original text untouched.
            output.append(lines[i])
            i += 1
            continue

        code = ''.join(code_lines).replace('\r\n', '\n')
        if code.endswith('\n'):
            code = code[:-1]

        placeholder = f'__MDSYNC_MERMAID_{marker}_{len(blocks) + 1:04d}__'
        indent = start_match.group(1)
        line_ending = current_eol or '\n'
        output.append(f'{indent}{placeholder}{line_ending}')
        blocks.append(MermaidBlock(placeholder=placeholder, code=code))

        i = j + 1

    return ''.join(output), blocks


def _parse_addon_attrs(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for key, value in re.findall(r'([a-zA-Z0-9_-]+)="(.*?)"', tag):
        attrs[key] = html.unescape(value)

    # Some fetch payloads return record as raw JSON in double-quoted attribute,
    # e.g. record="{"data":"..."}". The regex above truncates at the
    # first internal quote, so recover `record` from the original tag if needed.
    if not attrs.get('record'):
        start = tag.find('record="')
        if start != -1:
            start += len('record="')
            end = tag.rfind('"')
            if end > start:
                raw = tag[start:end]
                if raw.endswith('/'):
                    raw = raw[:-1]
                attrs['record'] = html.unescape(raw)
    elif attrs.get('record') == '{':
        start = tag.find('record="')
        if start != -1:
            start += len('record="')
            end = tag.rfind('"')
            if end > start:
                raw = tag[start:end]
                if raw.endswith('/'):
                    raw = raw[:-1]
                attrs['record'] = html.unescape(raw)
    return attrs


def _addon_tag_to_mermaid(tag: str) -> str | None:
    attrs = _parse_addon_attrs(tag)
    component_type_id = attrs.get('component-type-id') or attrs.get('component_type_id')
    if component_type_id != MERMAID_COMPONENT_TYPE_ID:
        return None

    record_raw = attrs.get('record')
    if not isinstance(record_raw, str):
        return None

    try:
        record = json.loads(record_raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(record, dict):
        return None

    if record.get('view') != MERMAID_VIEW:
        return None

    data = record.get('data')
    if not isinstance(data, str):
        return None

    code = data.replace('\r\n', '\n')
    return f'```mermaid\n{code}\n```'


def convert_addons_to_mermaid(markdown: str) -> tuple[str, int]:
    tag_pattern = re.compile(r'<add-ons\b[^>]*\/>')

    converted = 0
    output: list[str] = []

    for line in markdown.splitlines(keepends=True):
        text, eol = _split_line_ending(line)
        match = tag_pattern.search(text)
        if match is None:
            output.append(line)
            continue

        tag = match.group(0)
        mermaid = _addon_tag_to_mermaid(tag)
        if mermaid is None:
            output.append(line)
            continue

        replaced = text[:match.start()] + mermaid + text[match.end():]
        output.append(replaced + eol)
        converted += 1

    return ''.join(output), converted


def _normalize_fenced_block_trailing_blank_lines(markdown: str) -> str:
    lines = markdown.splitlines(keepends=True)
    output: list[str] = []

    fence_open = False
    fence_char = ''
    fence_len = 0
    fence_body: list[str] = []

    for line in lines:
        text, _ = _split_line_ending(line)

        if not fence_open:
            start = re.match(r'^[ \t]*(`{3,}|~{3,}).*$', text)
            if start is None:
                output.append(line)
                continue

            marker = start.group(1)
            fence_open = True
            fence_char = marker[0]
            fence_len = len(marker)
            fence_body = []
            output.append(line)
            continue

        close = re.match(rf'^[ \t]*{re.escape(fence_char)}{{{fence_len},}}[ \t]*$', text)
        if close is None:
            fence_body.append(line)
            continue

        while fence_body:
            body_text, _ = _split_line_ending(fence_body[-1])
            if body_text.strip() != '':
                break
            fence_body.pop()

        output.extend(fence_body)
        output.append(line)
        fence_open = False
        fence_char = ''
        fence_len = 0
        fence_body = []

    if fence_open and fence_body:
        output.extend(fence_body)

    return ''.join(output)


def canonicalize_markdown(markdown: str) -> tuple[str, int]:
    converted, converted_count = convert_addons_to_mermaid(markdown)
    normalized = converted.replace('\r\n', '\n')
    normalized = _normalize_fenced_block_trailing_blank_lines(normalized)
    if normalized.endswith('\n'):
        normalized = normalized[:-1]
    return normalized, converted_count


def _extract_block_text(item: dict[str, Any]) -> str:
    for value in item.values():
        if not isinstance(value, dict):
            continue
        elements = value.get('elements')
        if not isinstance(elements, list):
            continue

        parts: list[str] = []
        for element in elements:
            if not isinstance(element, dict):
                continue
            text_run = element.get('text_run')
            if isinstance(text_run, dict):
                content = text_run.get('content')
                if isinstance(content, str):
                    parts.append(content)

        if parts:
            return ''.join(parts)

    return ''


def _normalize_placeholder_text(text: str) -> str:
    normalized = text.strip()
    # markdown renderers may consume wrapper markers like __...__ or **...**.
    for _ in range(3):
        changed = False
        if len(normalized) >= 4 and normalized.startswith('**') and normalized.endswith('**'):
            normalized = normalized[2:-2].strip()
            changed = True
        if len(normalized) >= 4 and normalized.startswith('__') and normalized.endswith('__'):
            normalized = normalized[2:-2].strip()
            changed = True
        if not changed:
            break
    return normalized


def _list_doc_blocks(lark: LarkCLI, *, document_id: str, identity: str) -> list[dict[str, Any]]:
    payload = lark.run_json(
        [
            'api',
            'GET',
            f'/open-apis/docx/v1/documents/{document_id}/blocks',
            '--as',
            identity,
        ]
    )
    data = payload.get('data')
    if isinstance(data, dict):
        items = data.get('items')
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _locate_placeholder(
    *,
    placeholder: str,
    items: list[dict[str, Any]],
) -> tuple[str, str, int] | None:
    expected = placeholder.strip()
    expected_normalized = _normalize_placeholder_text(expected)

    items_by_id: dict[str, dict[str, Any]] = {
        item['block_id']: item
        for item in items
        if isinstance(item.get('block_id'), str)
    }

    for item in items:
        block_id = item.get('block_id')
        if not isinstance(block_id, str):
            continue

        text = _extract_block_text(item)
        actual = text.strip()
        if actual != expected and _normalize_placeholder_text(actual) != expected_normalized:
            continue

        parent_id = item.get('parent_id')
        if not isinstance(parent_id, str) or not parent_id:
            continue

        parent = items_by_id.get(parent_id)
        if not isinstance(parent, dict):
            continue

        children = parent.get('children')
        if not isinstance(children, list):
            continue

        try:
            index = children.index(block_id)
        except ValueError:
            continue

        return parent_id, block_id, index

    return None


def _dump_arg(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def replace_placeholder_blocks_with_addons(
    lark: LarkCLI,
    *,
    document_id: str,
    identity: str,
    blocks: list[MermaidBlock],
) -> list[dict[str, object]]:
    replacements: list[dict[str, object]] = []

    for block in blocks:
        items = _list_doc_blocks(lark, document_id=document_id, identity=identity)
        location = _locate_placeholder(placeholder=block.placeholder, items=items)
        if location is None:
            raise RuntimeError(f'failed to locate placeholder block: {block.placeholder}')

        parent_id, _, index = location

        lark.run_json(
            [
                'api',
                'DELETE',
                f'/open-apis/docx/v1/documents/{document_id}/blocks/{parent_id}/children/batch_delete',
                '--as',
                identity,
                '--data',
                _dump_arg({'start_index': index, 'end_index': index + 1}),
            ]
        )

        record = {
            'data': block.code,
            'theme': 'default',
            'view': MERMAID_VIEW,
        }
        create_payload = {
            'index': index,
            'children': [
                {
                    'block_type': 40,
                    'add_ons': {
                        'component_type_id': MERMAID_COMPONENT_TYPE_ID,
                        'record': json.dumps(record, ensure_ascii=False, separators=(',', ':')),
                    },
                }
            ],
        }

        lark.run_json(
            [
                'api',
                'POST',
                f'/open-apis/docx/v1/documents/{document_id}/blocks/{parent_id}/children',
                '--as',
                identity,
                '--data',
                _dump_arg(create_payload),
            ]
        )

        replacements.append(
            {
                'placeholder': block.placeholder,
                'parent_id': parent_id,
                'index': index,
                'code_length': len(block.code),
            }
        )

    return replacements
