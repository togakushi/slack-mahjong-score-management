import copy

import libs.global_value as g
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.commands import graph, ranking, report, results
from libs.functions import message
from libs.utils import dictutil


def main(m: MessageParserProtocol):

    if m.data.status != "message_append":
        return

    api_adapter = factory.select_adapter(g.selected_service)

    match m.command_type:
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
                api_adapter.post(m)
            elif versus_mode:  # 直接対戦
                results.versus.aggregation(m)
                api_adapter.post(m)
            else:  # 成績サマリ
                results.summary.aggregation(m)
                api_adapter.post(m)
        case "graph":
            g.params = dictutil.placeholder(g.cfg.graph, m)
            if len(g.params["player_list"]) == 1:  # 対象がひとり
                if g.params.get("statistics"):
                    count = graph.personal.statistics_plot(m)
                else:
                    count = graph.personal.plot(m)
            else:  # 対象が複数
                if g.params.get("rating"):  # レーティング
                    count = graph.rating.plot(m)
                else:
                    if g.params.get("order"):
                        count = graph.summary.rank_plot(m)
                    else:
                        count = graph.summary.point_plot(m)
            if count == 0:
                api_adapter.post_message(m)
            else:
                api_adapter.fileupload(m)
        case "ranking":
            g.params = dictutil.placeholder(g.cfg.ranking, m)
            if g.params.get("rating"):  # レーティング
                ranking.rating.aggregation(m)
                api_adapter.post(m)
            else:  # ランキング
                tmp_m = copy.deepcopy(m)
                tmp_m.post.message, m.post.message = ranking.ranking.aggregation(m)
                res = api_adapter.post_message(tmp_m)
                if m.post.message:
                    m.post.ts = str(res.get("ts", "undetermined"))
                    api_adapter.post_multi_message(m)
        case "report":
            g.params = dictutil.placeholder(g.cfg.report, m)
            m.post.message_type = "no_hits"
            if len(g.params["player_list"]) == 1:  # 成績レポート
                name, pdf_file = report.results_report.gen_pdf()
                if pdf_file:
                    m.post.file_list = [{f"成績レポート({name})": str(pdf_file)}]
                    api_adapter.fileupload(m)
                else:
                    m.post.message_type = "invalid_argument"
                    message.random_reply(m)
                    api_adapter.post_message(m)
            elif g.params.get("order"):
                if (file_path := report.winner.plot()):
                    m.post.file_list = [{"成績上位者": file_path}]
                    api_adapter.fileupload(m)
                else:
                    message.random_reply(m)
                    api_adapter.post_message(m)
            elif g.params.get("statistics"):
                if (file_path := report.monthly.plot()):
                    m.post.file_list = [{"月別ゲーム統計": file_path}]
                    api_adapter.fileupload(m)
                else:
                    message.random_reply(m)
                    api_adapter.post_message(m)
            elif g.params.get("versus_matrix") or len(g.params["player_list"]) >= 2:  # 対局対戦マトリックス
                m.post.headline, m.post.file_list = report.matrix.plot(m)
                message.random_reply(m)
                api_adapter.post(m)
            else:
                if (file_path := report.results_list.main()):
                    m.post.file_list = [{"成績一覧": file_path}]
                    api_adapter.fileupload(m)
                else:
                    message.random_reply(m)
                    api_adapter.post_message(m)
