"""
libs/commands/graph/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from libs.commands.graph import personal, rating, summary
from libs.utils import dictutil


def main():
    """グラフをslackにpostする"""
    api_adapter = factory.select_adapter(g.selected_service)

    g.params = dictutil.placeholder(g.cfg.graph)

    if len(g.params["player_list"]) == 1:  # 対象がひとり
        title = "個人成績"
        if g.params.get("statistics"):
            count, ret = personal.statistics_plot()
        else:
            count, ret = personal.plot()
    else:  # 対象が複数
        if g.params.get("rating"):  # レーティング
            title = "レーティング推移"
            count, ret = rating.plot()
        else:
            if g.params.get("order"):
                title = "順位変動"
                count, ret = summary.rank_plot()
            else:
                title = "ポイント推移"
                count, ret = summary.point_plot()

    if count == 0:
        api_adapter.post_message(ret)
    else:
        api_adapter.fileupload(title, ret)
