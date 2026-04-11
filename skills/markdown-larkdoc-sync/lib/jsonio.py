from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, TextIO


def dump_json(payload: Mapping[str, Any], stream: TextIO) -> None:
    json.dump(payload, stream, ensure_ascii=False, sort_keys=True, indent=2)
    stream.write('\n')
