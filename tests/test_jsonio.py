import io

from markdown_larkdoc_sync.jsonio import dump_json


def test_dump_json_is_utf8_sorted_and_newline_terminated():
    buffer = io.StringIO()

    dump_json({'z': 1, 'a': '中文'}, buffer)

    rendered = buffer.getvalue()

    assert '中文' in rendered
    assert '\\u4e2d\\u6587' not in rendered
    assert rendered.startswith('{\n  "a": "中文",\n  "z": 1\n}')
    assert rendered.index('"a"') < rendered.index('"z"')
    assert rendered.endswith('\n')
