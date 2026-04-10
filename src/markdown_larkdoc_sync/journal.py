from __future__ import annotations

from pathlib import Path
from typing import Any

from markdown_larkdoc_sync.jsonio import dump_json


class Journal:
    def __init__(self, git_dir: Path):
        self._git_dir = git_dir

    def write_run(self, run_id: str, payload: dict[str, Any]) -> Path:
        run_path = self._git_dir / 'markdown-larkdoc-sync' / 'runs' / f'{run_id}.json'
        run_path.parent.mkdir(parents=True, exist_ok=True)
        with run_path.open('w', encoding='utf-8') as stream:
            dump_json(payload, stream)
        return run_path
