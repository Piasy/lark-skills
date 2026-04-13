from __future__ import annotations

import json
import os
import subprocess
from json import JSONDecodeError
from collections.abc import Sequence
from pathlib import Path
from typing import Any


class LarkCLIError(RuntimeError):
    pass


class LarkCLI:
    def __init__(self, binary: str | None = None):
        self.binary = binary or os.environ.get('MARKDOWN_LARKDOC_SYNC_LARK_CLI', 'lark-cli')

    def _run(self, args: Sequence[str], *, cwd: str | Path | None = None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.binary, *args],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(cwd) if cwd is not None else None,
            )
        except FileNotFoundError as exc:
            raise LarkCLIError(str(exc)) from exc

    def run_json(self, args: Sequence[str], *, cwd: str | Path | None = None) -> dict[str, Any]:
        result = self._run(args, cwd=cwd)

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or 'lark-cli command failed'
            raise LarkCLIError(message)

        return json.loads(result.stdout)

    def run_text(self, args: Sequence[str], *, cwd: str | Path | None = None) -> str:
        result = self._run(args, cwd=cwd)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or 'lark-cli command failed'
            raise LarkCLIError(message)
        return result.stdout

    def list_profiles(self) -> list[str]:
        payload = self.run_json(['auth', 'list'])
        if not isinstance(payload, list):
            return []

        profiles: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            app_id = item.get('appId')
            if isinstance(app_id, str) and app_id and app_id not in profiles:
                profiles.append(app_id)
        return profiles

    def active_profile(self) -> str | None:
        raw = self.run_text(['config', 'show'])
        start = raw.find('{')
        end = raw.rfind('}')
        if start < 0 or end < start:
            return None

        try:
            payload = json.loads(raw[start : end + 1])
        except JSONDecodeError:
            return None

        profile = payload.get('profile') if isinstance(payload, dict) else None
        if not isinstance(profile, str):
            return None
        profile = profile.strip()
        return profile or None

    def resolve_profile(self, requested: str | None) -> str | None:
        if requested is not None:
            normalized = requested.strip()
            if normalized and normalized.lower() != 'auto':
                return normalized

        active = self.active_profile()
        if active:
            return active

        profiles = self.list_profiles()
        if len(profiles) == 1:
            return profiles[0]
        return None
