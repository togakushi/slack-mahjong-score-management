import os

import lib.function as f
from lib.function import global_value as g

from lib.command.graph import summary
from lib.command.graph import personal


def slackpost(client, channel, argument):
    """
    ポイント推移グラフをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    msg = f.message.invalid_argument()
    command_option = f.configure.command_option_initialization("graph")
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    if starttime or endtime:
        if len(target_player) == 1: # 描写対象がひとり → 個人成績
            command_option["guest_skip"] = False
            count = personal.plot(starttime, endtime, target_player, target_count, command_option)
        else: # 描写対象が複数 → 比較
            count = summary.plot(starttime, endtime, target_player, target_count, command_option)
        file = os.path.join(os.path.realpath(os.path.curdir), "graph.png")
        if count <= 0:
            f.slack_api.post_message(client, channel, f.message.no_hits(starttime, endtime))
        else:
            f.slack_api.post_fileupload(client, channel, "成績グラフ", file)
    else:
        f.slack_api.post_message(client, channel, msg)
