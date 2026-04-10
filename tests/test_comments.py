from markdown_larkdoc_sync.comments import build_resolve_payload, flatten_open_comments


def test_flatten_open_comments_skips_solved_cards():
    payload = {
        'items': [
            {'comment_id': 'c1', 'is_solved': False, 'reply_list': {'replies': [{'reply_id': 'r1'}]}},
            {'comment_id': 'c2', 'is_solved': True, 'reply_list': {'replies': [{'reply_id': 'r2'}]}},
        ]
    }

    items = flatten_open_comments(payload)
    assert [item['comment_id'] for item in items] == ['c1']


def test_build_resolve_payload_marks_comment_solved():
    payload = build_resolve_payload('doc_token', 'docx', 'c1')

    assert payload['params']['file_token'] == 'doc_token'
    assert payload['data']['file_type'] == 'docx'
    assert payload['data']['comment_id'] == 'c1'
    assert payload['data']['is_solved'] is True


def test_build_resolve_payload_schema_field_contract():
    payload = build_resolve_payload('doc_token', 'docx', 'c1')

    assert set(payload.keys()) == {'params', 'data'}
    assert set(payload['params'].keys()) == {'file_token'}
    assert set(payload['data'].keys()) == {'file_type', 'comment_id', 'is_solved'}
