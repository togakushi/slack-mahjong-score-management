import os

import lib.function as f
from lib.function import global_value as g

from lib.command.graph import summary
from lib.command.graph import personal


def help_message():
    graph_option = f.configure.command_option_initialization("graph")

    msg = [
        "*成績グラフヘルプ*",
        f"\t呼び出しキーワード： {g.commandword['graph']}",
        f"\t検索範囲デフォルト： {graph_option['aggregation_range'][0]}",
        "\tモード切替",
        "\t\t全体成績： 対象プレイヤー指定 0人",
        "\t\t個人成績： 対象プレイヤー指定 1人",
        "\t\t成績比較： 対象プレイヤー指定 2人以上",
        "\n*専用オプション*",
        "\t・順位",
    ]
    return("\n".join(msg))


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

    command_option = f.configure.command_option_initialization("graph")
    _, target_player, _, command_option = f.common.argument_analysis(argument, command_option)

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    # ヘルプ表示
    if command_option["help"]:
        return(help_message())

    if len(target_player) == 1: # 対象がひとり → 個人成績
        count, ret = personal.plot(argument, command_option)
    else: # 対象が複数 → 比較
        count, ret = summary.plot(argument, command_option)

    if count == 0:
        f.slack_api.post_message(client, channel, ret)
    else:
        f.slack_api.post_fileupload(client, channel, "成績グラフ", ret)
