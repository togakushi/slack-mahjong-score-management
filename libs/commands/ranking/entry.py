"""
libs/commands/ranking/entry.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from libs.commands import ranking
from libs.utils import dictutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """ランキング生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.data.status != "message_append":
        return

    g.params = dictutil.placeholder(g.cfg.ranking, m)

    if g.params.get("rating"):  # レーティング
        m.data.command_type = "rating"
        ranking.rating.aggregation(m)
    else:  # ランキング
        m.data.command_type = "ranking"
        ranking.ranking.aggregation(m)
