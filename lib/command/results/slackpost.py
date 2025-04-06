"""
lib/command/results/slackpost.py
"""

import lib.global_value as g
from lib import function as f
from lib.command.results import detail, rating, summary, versus
from lib.database.common import placeholder


def main():
    """成績の集計結果をslackにpostする"""
    g.params = placeholder(g.cfg.results)
    # モード切り替え
    versus_mode = False
    if g.cfg.results.versus_matrix:
        versus_mode = True
        if len(g.params["player_list"]) == 0:
            versus_mode = False
        if len(g.params["player_list"]) == 1 and not g.cfg.results.all_player:
            versus_mode = False

    # ---
    if len(g.params["player_list"]) == 1 and not versus_mode:  # 個人/チーム成績詳細
        msg1, msg2 = detail.aggregation()
        f.slack_api.slack_post(
            headline=msg1,
            message=msg2,
        )
    elif g.params.get("rating"):  # レーティング
        msg1, msg2, file_list = rating.aggregation()
        f.slack_api.slack_post(
            headline=msg1,
            message=msg2,
            summarize=False,
            file_list=file_list,
        )
    elif versus_mode:  # 直接対戦
        msg1, msg2, file_list = versus.aggregation()
        f.slack_api.slack_post(
            headline=msg1,
            message=msg2,
            file_list=file_list,
        )
    else:  # 成績サマリ
        headline, msg2, file_list = summary.aggregation()
        f.slack_api.slack_post(
            headline=headline,
            message=msg2,
            summarize=False,
            file_list=file_list,
        )
