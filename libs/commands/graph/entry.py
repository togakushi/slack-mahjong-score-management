"""
libs/commands/graph/entry.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from libs.commands import graph
from libs.utils import dictutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """グラフ生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    m.status.command_type = "graph"
    g.params = dictutil.placeholder(g.cfg.graph, m)

    if len(g.params["player_list"]) == 1:  # 対象がひとり
        if g.params.get("statistics"):
            graph.personal.statistics_plot(m)
        else:
            graph.personal.plot(m)
    else:  # 対象が複数
        if g.params.get("rating"):  # レーティング
            graph.rating.plot(m)
        else:
            if g.params.get("order"):
                graph.summary.rank_plot(m)
            else:
                graph.summary.point_plot(m)
