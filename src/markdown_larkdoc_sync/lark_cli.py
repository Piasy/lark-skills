from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Sequence
from typing import Any


class LarkCLIError(RuntimeError):
    pass


class LarkCLI:
    def __init__(self, binary: str | None = None):
        self.binary = binary or os.environ.get('MARKDOWN_LARKDOC_SYNC_LARK_CLI', 'lark-cli')

    def run_json(self, args: Sequence[str]) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [self.binary, *args],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise LarkCLIError(str(exc)) from exc

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or 'lark-cli command failed'
            raise LarkCLIError(message)

        return json.loads(result.stdout)
