"""
libs/commands/ranking/entry.py
"""

from typing import TYPE_CHECKING

import libs.global_value as g
from integrations.protocols import CommandType
from libs.commands import ranking
from libs.utils import dictutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def main(m: "MessageParserProtocol"):
    """ランキング生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    g.params = dictutil.placeholder(g.cfg.ranking, m)

    if g.params.get("rating"):  # レーティング
        m.status.command_type = CommandType.RATING
        ranking.rating.aggregation(m)
    else:  # ランキング
        m.status.command_type = CommandType.RANKING
        ranking.ranking.aggregation(m)
