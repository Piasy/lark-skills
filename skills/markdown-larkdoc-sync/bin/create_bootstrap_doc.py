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

from frontmatter import split_frontmatter
from jsonio import dump_json
from lark_cli import LarkCLI, LarkCLIError
from mermaid_addons import (
    canonicalize_markdown,
    contains_whiteboard,
    extract_remote_markdown,
    replace_mermaid_fences_with_placeholders,
    replace_placeholder_blocks_with_addons,
)


def _extract_doc_id(payload: dict[str, object]) -> str | None:
    data = payload.get('data')
    if not isinstance(data, dict):
        return None

    doc_id = data.get('doc_id')
    if isinstance(doc_id, str) and doc_id:
        return doc_id

    token = data.get('document_id')
    if isinstance(token, str) and token:
        return token

    return None


def _extract_doc_url(payload: dict[str, object]) -> str | None:
    data = payload.get('data')
    if not isinstance(data, dict):
        return None

    for key in ('doc_url', 'url'):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value

    return None


def _normalize_profile(value: str | None) -> str | None:
    if value is None:
        return None
    profile = value.strip()
    if not profile or profile.lower() == 'auto':
        return None
    return profile


def _build_create_args(
    *,
    title: str,
    identity: str,
    profile: str | None,
    folder_token: str | None,
    wiki_space: str | None,
    wiki_node: str | None,
) -> list[str]:
    args = [
        'docs',
        '+create',
        '--title',
        title,
        '--markdown',
        '@./bootstrap.md',
        '--as',
        identity,
    ]
    if profile:
        args.extend(['--profile', profile])
    if folder_token:
        args.extend(['--folder-token', folder_token])
    if wiki_space:
        args.extend(['--wiki-space', wiki_space])
    if wiki_node:
        args.extend(['--wiki-node', wiki_node])
    return args


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('--title', required=True)
    parser.add_argument('--identity', default='user')
    parser.add_argument('--profile')
    parser.add_argument('--folder-token')
    parser.add_argument('--wiki-space')
    parser.add_argument('--wiki-node')
    args = parser.parse_args()

    markdown_path = Path(args.markdown_path)
    markdown_text = markdown_path.read_text(encoding='utf-8')
    _, body = split_frontmatter(markdown_text)

    temp_root = Path(tempfile.mkdtemp(prefix='markdown-larkdoc-bootstrap-'))
    temp_markdown = temp_root / 'bootstrap.md'
    temp_markdown.write_text(body, encoding='utf-8')

    try:
        lark = LarkCLI()
        requested_profile = _normalize_profile(args.profile)
        available_profiles = lark.list_profiles()
        active_profile = lark.active_profile()

        effective_profile = requested_profile
        profile_resolution = 'requested' if requested_profile else 'auto'
        profile_warning: str | None = None

        if requested_profile and available_profiles and requested_profile not in available_profiles:
            if active_profile and active_profile in available_profiles:
                effective_profile = active_profile
                profile_resolution = 'fallback_active_profile'
            elif len(available_profiles) == 1:
                effective_profile = available_profiles[0]
                profile_resolution = 'fallback_single_profile'
            else:
                effective_profile = None

            if effective_profile:
                profile_warning = (
                    f'requested profile "{requested_profile}" not found; '
                    f'fallback to "{effective_profile}"'
                )

        if effective_profile is None:
            if active_profile:
                effective_profile = active_profile
                profile_resolution = 'active_profile'
            elif len(available_profiles) == 1:
                effective_profile = available_profiles[0]
                profile_resolution = 'single_profile'
            elif requested_profile:
                raise RuntimeError(
                    f'requested profile "{requested_profile}" not found and no fallback profile available; '
                    f'available profiles: {available_profiles}'
                )
            else:
                profile_resolution = 'cli_default'

        create_args = _build_create_args(
            title=args.title,
            identity=args.identity,
            profile=effective_profile,
            folder_token=args.folder_token,
            wiki_space=args.wiki_space,
            wiki_node=args.wiki_node,
        )

        try:
            create_result = lark.run_json(create_args, cwd=temp_root)
        except LarkCLIError as exc:
            message = str(exc)
            if (
                requested_profile
                and requested_profile == effective_profile
                and 'profile' in message
                and 'not found' in message
            ):
                fallback_profile = lark.resolve_profile(None)
                if fallback_profile and fallback_profile != requested_profile:
                    effective_profile = fallback_profile
                    profile_resolution = 'retry_fallback_after_profile_not_found'
                    profile_warning = (
                        f'requested profile "{requested_profile}" not found during create; '
                        f'retried with "{effective_profile}"'
                    )
                    create_result = lark.run_json(
                        _build_create_args(
                            title=args.title,
                            identity=args.identity,
                            profile=effective_profile,
                            folder_token=args.folder_token,
                            wiki_space=args.wiki_space,
                            wiki_node=args.wiki_node,
                        ),
                        cwd=temp_root,
                    )
                else:
                    # Last fallback: retry without --profile and rely on lark-cli default profile.
                    profile_resolution = 'retry_cli_default_after_profile_not_found'
                    profile_warning = (
                        f'requested profile "{requested_profile}" not found during create; '
                        'retried with lark-cli default profile'
                    )
                    effective_profile = lark.resolve_profile(None)
                    create_result = lark.run_json(
                        _build_create_args(
                            title=args.title,
                            identity=args.identity,
                            profile=None,
                            folder_token=args.folder_token,
                            wiki_space=args.wiki_space,
                            wiki_node=args.wiki_node,
                        ),
                        cwd=temp_root,
                    )
            else:
                raise

        if effective_profile is None:
            effective_profile = lark.resolve_profile(None)

        doc_id = _extract_doc_id(create_result)
        if not doc_id:
            raise RuntimeError('create doc result missing doc_id/document_id')

        # Bootstrap docs +create converts mermaid fences into whiteboard blocks.
        # Immediately rewrite the new doc using the same overwrite/add-on path used
        # by the regular sync flow, so first-linking is safe by default.
        transport_body, mermaid_blocks = replace_mermaid_fences_with_placeholders(body)
        rewrite_markdown = temp_root / 'bootstrap-normalized.md'
        rewrite_markdown.write_text(transport_body, encoding='utf-8')

        update_result = lark.run_json(
            [
                'docs',
                '+update',
                '--doc',
                doc_id,
                '--as',
                args.identity,
                '--mode',
                'overwrite',
                '--markdown',
                '@./bootstrap-normalized.md',
            ],
            cwd=temp_root,
        )

        addon_replacements = replace_placeholder_blocks_with_addons(
            lark,
            document_id=doc_id,
            identity=args.identity,
            blocks=mermaid_blocks,
        )

        fetch_result = lark.run_json(
            [
                'docs',
                '+fetch',
                '--doc',
                doc_id,
                '--as',
                args.identity,
                '--format',
                'json',
            ]
        )
        remote_markdown = extract_remote_markdown(fetch_result) or ''

        remote_canonical, remote_addons_converted = canonicalize_markdown(remote_markdown)
        local_canonical, _ = canonicalize_markdown(body)
        normalized_verified = remote_canonical == local_canonical
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    payload: dict[str, object] = {
        'identity': args.identity,
        'title': args.title,
        'requested_profile': requested_profile,
        'effective_profile': effective_profile,
        'profile_resolution': profile_resolution,
        'available_profiles': available_profiles,
        'doc_id': doc_id,
        'doc_url': _extract_doc_url(create_result),
        'created_with_markdown': str(markdown_path),
        'local_body_length': len(body),
        'mode': 'overwrite',
        'mermaid_block_count': len(mermaid_blocks),
        'addon_replacements': addon_replacements,
        'contains_whiteboard': contains_whiteboard(remote_markdown),
        'remote_addons_converted': remote_addons_converted,
        'normalized_verified': normalized_verified,
        'remote_markdown_preview': remote_markdown[:400],
        'update_result': update_result,
        'auto_normalized': True,
        'bootstrap_warning': (
            'create_bootstrap_doc now auto-runs overwrite + mermaid add-on rewrite. '
            'If normalized_verified is false, stop and investigate before proceeding.'
        ),
    }
    if profile_warning:
        payload['profile_warning'] = profile_warning
    if not normalized_verified:
        payload['reason'] = 'bootstrap normalization verification failed: remote canonical markdown differs from local body'

    dump_json(payload, sys.stdout)
    return 0 if normalized_verified else 2


if __name__ == '__main__':
    raise SystemExit(main())
