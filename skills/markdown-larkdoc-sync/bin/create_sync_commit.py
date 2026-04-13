from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
LIB = SKILL_ROOT / 'lib'

if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from git_sync import build_sync_message, resolve_repo_root, to_repo_relative_markdown_path
from jsonio import dump_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('markdown_path')
    parser.add_argument('declared_doc')
    parser.add_argument('identity')
    parser.add_argument('resolved_file_type')
    parser.add_argument('resolved_doc_token')
    parser.add_argument('profile')
    args = parser.parse_args()

    cwd = Path.cwd()
    repo_root = resolve_repo_root(cwd)
    normalized_markdown_path = to_repo_relative_markdown_path(
        args.markdown_path,
        repo_root=repo_root,
        cwd=cwd,
    )

    subprocess.run(['git', 'add', normalized_markdown_path], check=True)
    subprocess.run(
        [
            'git',
            'commit',
            '-m',
            build_sync_message(
                markdown_path=normalized_markdown_path,
                declared_doc=args.declared_doc,
                identity=args.identity,
                resolved_file_type=args.resolved_file_type,
                resolved_doc_token=args.resolved_doc_token,
                profile=args.profile,
            ),
            '--',
            normalized_markdown_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    commit = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dump_json({'commit': commit}, sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
