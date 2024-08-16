import lib.function as f
from lib.command.results import personal, summary, team, versus
from lib.function import global_value as g


def main(client, channel, argument):
    """
    成績の集計結果をslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    g.opt.initialization("results", argument)
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
    if len(g.prm.player_list) == 1 and not versus_mode:  # 個人成績
        msg1, msg2 = personal.aggregation()
        if g.args.testcase:
            f.common.debug_out(msg1, msg2)
        else:
            f.slack_api.slack_post(
                client=client,
                channel=channel,
                headline=msg1,
                message=msg2,
            )
    elif versus_mode:  # 直接対戦
        msg1, msg2, file_list = versus.aggregation()
        if g.args.testcase:
            f.common.debug_out(msg1, msg2)
        else:
            f.slack_api.slack_post(
                client=client,
                channel=channel,
                headline=msg1,
                message=msg2,
                file_list=file_list,
            )
    else:  # 成績サマリ
        if g.opt.team_total:
            msg1, msg2, file_list = team.aggregation()
        else:
            msg1, msg2, file_list = summary.aggregation()

        if g.args.testcase:
            f.common.debug_out(msg1, msg2)
        else:
            f.slack_api.slack_post(
                client=client,
                channel=channel,
                headline=msg1,
                message=msg2,
                summarize=False,
                file_list=file_list,
            )
