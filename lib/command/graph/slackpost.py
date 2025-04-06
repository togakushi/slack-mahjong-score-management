"""
lib/command/graph/slackpost.py
"""

import lib.global_value as g
from lib import function as f
from lib.command.graph import personal, rating, summary
from lib.database.common import placeholder


def main():
    """グラフをslackにpostする"""
    g.params = placeholder(g.cfg.graph)
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
        f.slack_api.post_message(ret)
    else:
        f.slack_api.post_fileupload(title, ret)
