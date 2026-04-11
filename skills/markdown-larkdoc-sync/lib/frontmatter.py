from __future__ import annotations

from dataclasses import dataclass
import re


ALLOWED_TOP_KEYS = ('title', 'markdown_larkdoc_sync')
ALLOWED_BINDING_KEYS = ('doc', 'as', 'profile')
ALLOWED_AS = ('user', 'bot')
_FRONTMATTER_PATTERN = re.compile(r'^---(?:\r?\n)(.*?)(?:\r?\n)---(?:\r?\n|$)', re.DOTALL)


class FrontmatterError(ValueError):
    pass


@dataclass(frozen=True)
class Binding:
    doc: str | None
    identity: str | None
    profile: str | None


def _parse_scalar(raw: str) -> str | None:
    value = raw.strip()
    if value in ('null', 'Null', 'NULL', '~'):
        return None
    if not value:
        return None
    if value[0] in {'"', "'"} and value[-1] == value[0] and len(value) >= 2:
        return value[1:-1]
    return value


def parse_frontmatter(frontmatter_text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_nested: dict[str, str | None] | None = None

    for raw_line in frontmatter_text.splitlines():
        if not raw_line.strip():
            continue
        if raw_line.lstrip().startswith(('-', '[', ']')):
            raise FrontmatterError('unsupported sequence style in frontmatter')

        indent = len(raw_line) - len(raw_line.lstrip(' '))
        line = raw_line.strip()
        if ':' not in line:
            raise FrontmatterError('invalid frontmatter line')
        key, value = line.split(':', 1)
        key = key.strip()

        if indent == 0:
            if key not in ALLOWED_TOP_KEYS:
                raise FrontmatterError(f'unsupported top-level key: {key}')
            if key == 'markdown_larkdoc_sync':
                if value.strip():
                    raise FrontmatterError('markdown_larkdoc_sync must be a mapping')
                nested: dict[str, str | None] = {}
                result[key] = nested
                current_nested = nested
            else:
                parsed = _parse_scalar(value)
                result[key] = parsed
                current_nested = None
            continue

        if indent == 2 and current_nested is not None:
            if key not in ALLOWED_BINDING_KEYS:
                raise FrontmatterError(f'unsupported binding key: {key}')
            parsed = _parse_scalar(value)
            current_nested[key] = parsed
            continue

        raise FrontmatterError('unsupported indentation structure in frontmatter')

    binding = result.get('markdown_larkdoc_sync')
    if isinstance(binding, dict):
        as_value = binding.get('as')
        if as_value is not None and as_value not in ALLOWED_AS:
            raise FrontmatterError('as must be user or bot')
    return result


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    match = _FRONTMATTER_PATTERN.match(text)
    if match is None:
        return {}, text

    frontmatter_text = match.group(1)
    body = text[match.end():].lstrip('\r\n')
    return parse_frontmatter(frontmatter_text), body


def extract_binding(frontmatter: dict[str, object]) -> Binding:
    nested = frontmatter.get('markdown_larkdoc_sync')
    if not isinstance(nested, dict):
        return Binding(doc=None, identity=None, profile=None)
    return Binding(
        doc=nested.get('doc') if isinstance(nested.get('doc'), str) else None,
        identity=nested.get('as') if isinstance(nested.get('as'), str) else None,
        profile=nested.get('profile') if isinstance(nested.get('profile'), str) else None,
    )


def _serialize_scalar(value: str | None) -> str:
    if value is None:
        return 'null'
    return value


def render_frontmatter(title: str | None, doc: str | None, identity: str | None, profile: str | None) -> str:
    lines = ['---']
    if title is not None:
        lines.append(f'title: {_serialize_scalar(title)}')
    lines.append('markdown_larkdoc_sync:')
    if doc is not None:
        lines.append(f'  doc: {_serialize_scalar(doc)}')
    if identity is not None:
        lines.append(f'  as: {_serialize_scalar(identity)}')
    if profile is not None:
        lines.append(f'  profile: {_serialize_scalar(profile)}')
    lines.append('---')
    return '\n'.join(lines)


def write_frontmatter_to_text(
    *,
    body: str,
    title: str | None,
    doc: str,
    identity: str,
    profile: str,
) -> str:
    if identity not in ALLOWED_AS:
        raise FrontmatterError('as must be user or bot')
    head = render_frontmatter(title=title, doc=doc, identity=identity, profile=profile)
    normalized_body = body if body.endswith('\n') or body == '' else f'{body}\n'
    return f'{head}\n\n{normalized_body}'
