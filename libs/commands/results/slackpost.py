"""
libs/commands/results/slackpost.py
"""

import libs.global_value as g
from integrations import factory
from libs.commands import results
from libs.utils import dictutil


def main():
    """成績の集計結果をslackにpostする"""
    api_adapter = factory.select_adapter(g.selected_service)

    g.params = dictutil.placeholder(g.cfg.results)

    # モード切り替え
    versus_mode = False
    if g.params.get("versus_matrix"):
        versus_mode = True
        if len(g.params["competition_list"]) == 0:  # 対戦相手リストが空ならOFF
            versus_mode = False

    # ---
    if len(g.params["player_list"]) == 1 and not versus_mode:  # 個人/チーム成績詳細
        msg1, msg2 = results.detail.aggregation()
        api_adapter.post(
            headline=msg1,
            message=msg2,
        )
    elif versus_mode:  # 直接対戦
        msg1, msg2, file_list = results.versus.aggregation()
        api_adapter.post(
            headline=msg1,
            message=msg2,
            file_list=file_list,
        )
    else:  # 成績サマリ
        headline, msg2, file_list = results.summary.aggregation()
        api_adapter.post(
            headline=headline,
            message=msg2,
            summarize=False,
            file_list=file_list,
        )
