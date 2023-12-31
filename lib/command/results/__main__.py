import lib.function as f
from lib.function import global_value as g

from lib.command.results import summary
from lib.command.results import personal
from lib.command.results import versus


def slackpost(client, channel, event_ts, argument, command_option):
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

    command_option : dict
        コマンドオプション
    """

    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    if starttime and endtime:
        # モード切り替え
        versus_mode = False
        if command_option["versus_matrix"]:
            versus_mode = True
            if len(target_player) == 0:
                versus_mode = False
            if len(target_player) == 1 and not command_option["all_player"]:
                versus_mode = False
        if len(target_player) == 1 and not versus_mode: # 個人成績
            msg1, msg2 = personal.aggregation(argument, command_option)
            res = f.slack_api.post_message(client, channel, msg1)
            for m in msg2.keys():
                f.slack_api.post_message(client, channel, msg2[m] + '\n', res["ts"])
        elif versus_mode: # 直接対戦
            msg1, msg2 = versus.aggregation(starttime, endtime, target_player, target_count, command_option)
            res = f.slack_api.post_message(client, channel, msg1)
            for m in msg2.keys():
                f.slack_api.post_message(client, channel, msg2[m] + '\n', res["ts"])
        else: # 成績サマリ
            msg1, msg2, msg3 = summary.aggregation(argument, command_option)
            res = f.slack_api.post_message(client, channel, msg2)
            if msg1:
                f.slack_api.post_text(client, channel, res["ts"], "", msg1)
            if msg3:
                f.slack_api.post_message(client, channel, msg3, res["ts"])
