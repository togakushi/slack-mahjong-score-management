import re

import lib.function as f
import lib.database as d
from lib.function import global_value as g


def aggregation(argument, command_option):
    """
    各チームの通算ポイントを表示

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg2 : text
        検索条件などの情報

    msg : dict
        集計結果

    file_list : dict
        ファイル出力用path
    """

    ### データ収集 ###
    params, game_info = f.common.game_info(argument, command_option)
    df_summary = d.aggregate.team_total(argument, command_option)
    df_summary = df_summary.rename(
        columns = {
            "team": "チーム名",
            "total": "通算ポイント",
            "rank": "平均順位",
            "count": "ゲーム数",
        }
    )

    ### 表示 ###
    msg = {}
    header = "*【チーム成績サマリ】*\n"
    header += f.message.header(game_info, command_option, params, "", 1)
    file_list = {}

    if not df_summary.empty:
        data = df_summary.to_markdown(
            index = False,
            tablefmt = "simple",
            numalign = "right",
            maxheadercolwidths = 16,
            floatfmt = ("", "+.1f", ".2f", "")
        )
        data = re.sub(r" -([0-9]+)", r"▲\1", data)
        msg[0] = f"```\n{data}\n```"

    return(header, msg, file_list)
