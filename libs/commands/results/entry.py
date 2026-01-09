"""
libs/commands/results/entry.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from integrations.protocols import CommandType
from libs.commands import results
from libs.utils import dictutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """成績集計処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    m.status.command_type = CommandType.RESULTS
    g.params = dictutil.placeholder(g.cfg.results, m)

    if g.params.get("versus_matrix", False) and g.params["competition_list"]:
        results.versus.aggregation(m)  # 直接対戦
    elif g.params.get("score_comparisons", False):
        results.summary.difference(m)  # 成績サマリ(差分モード)
    elif g.params["competition_list"]:
        results.detail.comparison(m)  # 成績詳細(比較)
    elif g.params["player_list"]:
        results.detail.aggregation(m)  # 成績詳細(単独)
    else:
        results.summary.aggregation(m)  # 成績サマリ(通常モード)
