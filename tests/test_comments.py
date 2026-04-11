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
    assert items[0]['reply_list']['replies'][0]['reply_id'] == 'r1'


def test_flatten_open_comments_reads_lark_cli_wrapped_payload():
    payload = {
        'code': 0,
        'data': {
            'items': [
                {'comment_id': 'c1', 'is_solved': False, 'reply_list': {'replies': [{'reply_id': 'r1'}]}},
                {'comment_id': 'c2', 'is_solved': True},
            ]
        },
        'msg': 'Success',
    }

    items = flatten_open_comments(payload)

    assert [item['comment_id'] for item in items] == ['c1']
    assert items[0]['reply_list']['replies'][0]['reply_id'] == 'r1'


def test_build_resolve_payload_marks_comment_solved():
    payload = build_resolve_payload('doc_token', 'docx', 'c1')

    assert payload['params']['file_token'] == 'doc_token'
    assert payload['params']['comment_id'] == 'c1'
    assert payload['params']['file_type'] == 'docx'
    assert payload['data']['is_solved'] is True


def test_build_resolve_payload_schema_field_contract():
    payload = build_resolve_payload('doc_token', 'docx', 'c1')

    assert set(payload.keys()) == {'params', 'data'}
    assert set(payload['params'].keys()) == {'file_token', 'comment_id', 'file_type'}
    assert set(payload['data'].keys()) == {'is_solved'}


def test_collect_open_comment_ids_returns_all_unsolved_ids():
    payload = {
        'data': {
            'items': [
                {'comment_id': 'c1', 'is_solved': False},
                {'comment_id': 'c2', 'is_solved': True},
                {'comment_id': 'c3', 'is_solved': False},
            ]
        }
    }

    from markdown_larkdoc_sync.comments import collect_open_comment_ids

    assert collect_open_comment_ids(payload) == ['c1', 'c3']
