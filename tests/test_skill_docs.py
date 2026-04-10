from pathlib import Path


def test_skill_mentions_single_v2_flow_and_subagent_review():
    content = Path('skills/markdown-larkdoc-sync/SKILL.md').read_text(encoding='utf-8')

    assert '只支持一个手动触发的 V2 工作流' in content
    assert '一致性审校必须由独立 sub-agent 执行' in content
    assert '成功收尾时要解决全部未解决评论' in content
