import lib.function as f
from lib.function import global_value as g

from lib.command.graph import summary
from lib.command.graph import personal


def main(client, channel, argument):
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

    g.logging.info(f"{argument=}")
    g.logging.info(f"{command_option=}")

    if len(target_player) == 1: # 対象がひとり → 個人成績
        count, ret = personal.plot(argument, command_option)
    else: # 対象が複数 → 比較
        if command_option["order"]:
            count, ret = summary.rank_plot(argument, command_option)
        else:
            count, ret = summary.point_plot(argument, command_option)

    if count == 0:
        f.slack_api.post_message(client, channel, ret)
    else:
        f.slack_api.post_fileupload(client, channel, "成績グラフ", ret)
