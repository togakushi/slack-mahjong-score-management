"""
libs/commands/results/entry.py
"""

import libs.global_value as g
from integrations.protocols import MessageParserProtocol
from libs.commands.results import detail, summary, versus
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """成績サマリ生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.data.status != "message_append":
        return

    m.data.command_type = "results"
    g.params = dictutil.placeholder(g.cfg.results, m)

    # モード切り替え
    versus_mode = False
    if g.params.get("versus_matrix"):
        versus_mode = True
        if len(g.params["competition_list"]) == 0:  # 対戦相手リストが空ならOFF
            versus_mode = False
    # ---
    if len(g.params["player_list"]) == 1 and not versus_mode:  # 個人/チーム成績詳細
        detail.aggregation(m)
    elif versus_mode:  # 直接対戦
        versus.aggregation(m)
    else:  # 成績サマリ
        summary.aggregation(m)
