"""
libs/commands/graph/slackpost.py
"""

import libs.global_value as g
from libs.commands.graph import personal, rating, summary
from libs.functions import slack_api
from libs.utils import dictutil


def main():
    """グラフをslackにpostする"""
    g.params.clear()
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
        slack_api.post_message(ret)
    else:
        slack_api.post_fileupload(title, ret)
