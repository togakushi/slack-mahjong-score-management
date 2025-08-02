"""
libs/commands/dispatcher.py
"""

import libs.global_value as g
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.commands import graph, ranking, report, results
from libs.utils import dictutil


def main(m: MessageParserProtocol, command_type: str):
    """サブコマンドディスパッチャー

    Args:
        m (MessageParserProtocol): メッセージデータ
        command_type (str): サブコマンドタイプ
    """

    if m.data.status != "message_append":
        return

    api_adapter = factory.select_adapter(g.selected_service)

    match command_type:
        case "results":
            g.params = dictutil.placeholder(g.cfg.results, m)
            # モード切り替え
            versus_mode = False
            if g.params.get("versus_matrix"):
                versus_mode = True
                if len(g.params["competition_list"]) == 0:  # 対戦相手リストが空ならOFF
                    versus_mode = False
            # ---
            if len(g.params["player_list"]) == 1 and not versus_mode:  # 個人/チーム成績詳細
                results.detail.aggregation(m)
            elif versus_mode:  # 直接対戦
                results.versus.aggregation(m)
            else:  # 成績サマリ
                results.summary.aggregation(m)
        case "graph":
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
        case "ranking":
            g.params = dictutil.placeholder(g.cfg.ranking, m)
            if g.params.get("rating"):  # レーティング
                ranking.rating.aggregation(m)
            else:  # ランキング
                ranking.ranking.aggregation(m)
        case "report":
            g.params = dictutil.placeholder(g.cfg.report, m)
            if len(g.params["player_list"]) == 1:  # 成績レポート
                report.results_report.gen_pdf(m)
            elif g.params.get("order"):
                report.winner.plot(m)
            elif g.params.get("statistics"):
                report.monthly.plot(m)
            elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
                report.matrix.plot(m)
            else:
                report.results_list.main(m)

    api_adapter.post(m)
