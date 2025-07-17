"""
libs/commands/graph/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.commands.graph import personal, rating, summary
from libs.utils import dictutil


def main(m: MessageParserProtocol):
    """グラフをslackにpostする

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)
    g.params = dictutil.placeholder(g.cfg.graph, m)

    if len(g.params["player_list"]) == 1:  # 対象がひとり
        m.post.title = "個人成績"
        if g.params.get("statistics"):
            count, ret = personal.statistics_plot(m)
        else:
            count, ret = personal.plot(m)
    else:  # 対象が複数
        if g.params.get("rating"):  # レーティング
            m.post.title = "レーティング推移"
            count, ret = rating.plot(m)
        else:
            if g.params.get("order"):
                m.post.title = "順位変動"
                count, ret = summary.rank_plot(m)
            else:
                m.post.title = "ポイント推移"
                count, ret = summary.point_plot(m)

    if count == 0:
        m.post.message = ret
        m.post.thread = False
        api_adapter.post_message(m)
    else:
        m.post.file_list = [{m.post.title: ret}]
        m.post.thread = False
        api_adapter.fileupload(m)
