import global_value as g
from lib import function as f
from lib.command.results import detail, rating, summary, versus


def main():
    """成績の集計結果をslackにpostする
    """

    g.opt.initialization("results", g.msg.argument)
    g.prm.update(g.opt)

    # モード切り替え
    versus_mode = False
    if g.opt.versus_matrix:
        versus_mode = True
        if len(g.prm.player_list) == 0:
            versus_mode = False
        if len(g.prm.player_list) == 1 and not g.opt.all_player:
            versus_mode = False

    # ---
    if len(g.prm.player_list) == 1 and not versus_mode:  # 個人/チーム成績詳細
        msg1, msg2 = detail.aggregation()
        f.slack_api.slack_post(
            headline=msg1,
            message=msg2,
        )
    elif g.opt.rating:  # レーティング
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
