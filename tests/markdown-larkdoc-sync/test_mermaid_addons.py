from mermaid_addons import (
    MERMAID_COMPONENT_TYPE_ID,
    _locate_placeholder,
    convert_addons_to_mermaid,
    replace_mermaid_fences_with_placeholders,
)


def test_replace_mermaid_fences_with_placeholders_extracts_code_blocks():
    body = (
        '# T\n\n'
        '```mermaid\n'
        'flowchart LR\n'
        '  A --> B\n'
        '```\n\n'
        'text\n'
    )

    transport, blocks = replace_mermaid_fences_with_placeholders(body)

    assert len(blocks) == 1
    assert blocks[0].code == 'flowchart LR\n  A --> B'
    assert blocks[0].placeholder in transport
    assert '```mermaid' not in transport


def test_convert_addons_to_mermaid_converts_code_chart_addon():
    source = (
        '<add-ons '
        f'component-type-id="{MERMAID_COMPONENT_TYPE_ID}" '
        'record="{&quot;data&quot;:&quot;flowchart LR\\n  A --&gt; B&quot;,&quot;theme&quot;:&quot;default&quot;,&quot;view&quot;:&quot;codeChart&quot;}"/>'
        '\n'
    )

    converted, count = convert_addons_to_mermaid(source)

    assert count == 1
    assert converted == '```mermaid\nflowchart LR\n  A --> B\n```\n'


def test_convert_addons_to_mermaid_ignores_non_code_chart_addon():
    source = (
        '<add-ons '
        f'component-type-id="{MERMAID_COMPONENT_TYPE_ID}" '
        'record="{&quot;data&quot;:&quot;flowchart LR\\n  A --&gt; B&quot;,&quot;theme&quot;:&quot;default&quot;,&quot;view&quot;:&quot;raw&quot;}"/>'
        '\n'
    )

    converted, count = convert_addons_to_mermaid(source)

    assert count == 0
    assert converted == source


def test_convert_addons_to_mermaid_supports_unescaped_record_attribute():
    source = (
        '<add-ons '
        f'component-type-id="{MERMAID_COMPONENT_TYPE_ID}" '
        'record="{"data":"flowchart LR\\n  A --\\u003e B","theme":"default","view":"codeChart"}"/>'
        '\n'
    )

    converted, count = convert_addons_to_mermaid(source)

    assert count == 1
    assert converted == '```mermaid\nflowchart LR\n  A --> B\n```\n'


def test_locate_placeholder_accepts_legacy_wrapped_placeholder_text():
    placeholder = '__MDSYNC_MERMAID_deadbeef_0001__'
    items = [
        {
            'block_id': 'root',
            'block_type': 1,
            'parent_id': '',
            'children': ['p_1'],
            'page': {'elements': []},
        },
        {
            'block_id': 'p_1',
            'block_type': 2,
            'parent_id': 'root',
            'text': {
                'elements': [
                    {
                        'text_run': {
                            # docx markdown rendering can consume surrounding __...__ emphasis markers
                            'content': 'MDSYNC_MERMAID_deadbeef_0001',
                        }
                    }
                ]
            },
        },
    ]

    location = _locate_placeholder(placeholder=placeholder, items=items)

    assert location == ('root', 'p_1', 0)


def test_canonicalize_markdown_normalizes_extra_blank_before_fence_close():
    source = (
        '```bash\n'
        'echo hi\n'
        '\n'
        '\n'
        '```\n'
    )

    converted, count = convert_addons_to_mermaid(source)

    # keep behavior stable for non-addon inputs
    assert count == 0
    assert converted == source

    from mermaid_addons import canonicalize_markdown

    canonical, _ = canonicalize_markdown(source)
    assert canonical == '```bash\necho hi\n```'
