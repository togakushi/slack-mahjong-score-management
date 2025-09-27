"""
libs/commands/report/entry.py
"""

import libs.global_value as g
from integrations.protocols import MessageParserProtocol
from libs.commands.report import (matrix, monthly, results_list,
                                  results_report, winner)
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """レポート生成処理エントリーポイント

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    if m.data.status != "message_append":
        return

    m.data.command_type = "report"
    g.params = dictutil.placeholder(g.cfg.report, m)

    if len(g.params["player_list"]) == 1:  # 成績レポート
        results_report.gen_pdf(m)
    elif g.params.get("order"):
        winner.plot(m)
    elif g.params.get("statistics"):
        monthly.plot(m)
    elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
        matrix.plot(m)
    else:
        results_list.main(m)
