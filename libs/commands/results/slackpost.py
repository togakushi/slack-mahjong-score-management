"""
libs/commands/results/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.commands import results
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """成績集計結果

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.data.status != "message_append":
        return

    api_adapter = factory.select_adapter(g.selected_service)
    g.params = dictutil.placeholder(g.cfg.results, m)

    # モード切り替え
    versus_mode = False
    if g.params.get("versus_matrix"):
        versus_mode = True
        if len(g.params["competition_list"]) == 0:  # 対戦相手リストが空ならOFF
            versus_mode = False

    # ---
    if len(g.params["player_list"]) == 1 and not versus_mode:  # 個人/チーム成績詳細
        m.post.headline, m.post.message = results.detail.aggregation(m)
        api_adapter.post(m)
    elif versus_mode:  # 直接対戦
        m.post.headline, m.post.message, m.post.file_list = results.versus.aggregation()
        api_adapter.post(m)
    else:  # 成績サマリ
        m.post.headline, m.post.message, m.post.file_list = results.summary.aggregation(m)
        m.post.summarize = False
        api_adapter.post(m)
