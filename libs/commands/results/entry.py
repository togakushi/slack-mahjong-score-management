"""
libs/commands/results/entry.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from libs.commands import results
from libs.utils import dictutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """成績集計処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    m.status.command_type = "results"
    g.params = dictutil.placeholder(g.cfg.results, m)

    # モード切り替え
    versus_mode = False
    if g.params.get("versus_matrix"):
        versus_mode = True
        if not g.params["competition_list"]:  # 対戦相手リストが空ならOFF
            versus_mode = False

    # ---
    if versus_mode and g.params["player_list"]:
        results.versus.aggregation(m)  # 直接対戦
    elif g.params.get("score_comparisons", False):
        results.summary.aggregation(m)  # 成績サマリ
    elif g.params["competition_list"]:
        results.detail.comparison(m)  # 成績詳細(比較)
    elif g.params["player_list"]:
        results.detail.aggregation(m)  # 成績詳細(単独)
    else:
        results.summary.aggregation(m)  # 成績サマリ
