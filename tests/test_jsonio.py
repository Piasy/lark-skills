import io
import json

from markdown_larkdoc_sync.jsonio import dump_json


def test_dump_json_is_utf8_sorted_and_newline_terminated():
    buffer = io.StringIO()

    dump_json({'z': 1, 'a': '中文'}, buffer)

    payload = json.loads(buffer.getvalue())
    assert payload == {'a': '中文', 'z': 1}
    assert buffer.getvalue().index('a') < buffer.getvalue().index('z')
    assert buffer.getvalue().endswith('\n')
