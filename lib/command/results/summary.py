import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def aggregation(argument, command_option):
    """
    各プレイヤーの累積ポイントを表示

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        集計結果

    msg2 : text
        検索条件などの情報

    msg3 : text
        メモ内容
    """

    ### データ収集 ###
    params = d.common.placeholder_params(argument, command_option)
    total_game_count, first_game, last_game = d.aggregate.game_count(argument, command_option)
    summary_data = d.aggregate.game_summary(argument, command_option)

    ### 表示 ###
    if total_game_count == 0: # 結果が0件のとき
        return(None, f.message.no_hits(argument, command_option), None)

    # --- 情報ヘッダ
    msg2 = "*【成績サマリ】*\n"
    if params["target_count"] == 0: # 直近指定がない場合は検索範囲を付ける
        msg2 += f"\t検索範囲：{first_game} ～ {last_game}\n".replace("-", "/")
    msg2 += f"\t最初のゲーム：{first_game}\n\t最後のゲーム：{last_game}\n".replace("-", "/")

    if params["player_name"]:
        msg2 += f"\t総ゲーム数：{total_game_count} 回"
    else:
        msg2 += f"\tゲーム数：{total_game_count} 回"

    if g.config["mahjong"].getboolean("ignore_flying", False):
        msg2 += "\n"
    else:
        msg2 += " / トバされた人（延べ）： {} 人\n".format(
            summary_data["flying"].sum(),
        )
    msg2 += "\t" + f.message.remarks(command_option)

    # --- 集計結果
    msg3 = ""
    padding = c.member.CountPadding(list(summary_data["表示名"].unique()))
    if command_option["score_comparisons"]: # 差分表示
        msg1 = "## {} {}： 累積    / 点差 ##\n".format(
            "名前", " " * (padding - f.common.len_count("名前") - 4),
        )
        for _, row in summary_data.iterrows():
            msg1 += "{}： {:>+6.1f} / {:>5.1f}\n".format(
                row["表示名"], row["pt_total"], row["pt_diff"],
            ).replace("-", "▲")
    else: # 通常表示
        if g.config["mahjong"].getboolean("ignore_flying", False): # トビカウントなし
            msg1 = "# {} {} :  累積   (平均)  / 順位分布 (平均) #\n".format(
                "名前", " " * (padding - f.common.len_count("名前") - 3))
            for _, row in summary_data.iterrows():
                msg1 += "{}： {:>+6.1f} ({:>+5.1f}) / {}*{}*{}*{} ({:1.2f})\n".format(
                    row["表示名"], row["pt_total"], row["pt_avg"],
                    row["1st"], row["2nd"], row["3rd"], row["4th"],
                    row["rank_avg"],
                ).replace("-", "▲").replace("*", "-")
        else:
            msg1 = "# {} {} :  累積   (平均)  / 順位分布 (平均) / トビ #\n".format(
                "名前", " " * (padding - f.common.len_count("名前") - 3))
            for index, row in summary_data.iterrows():
                msg1 += "{}： {:>+6.1f} ({:>+5.1f}) / {}*{}*{}*{} ({:1.2f}) / {}\n".format(
                    row["表示名"], row["pt_total"], row["pt_avg"],
                    row["1st"], row["2nd"], row["3rd"], row["4th"],
                    row["rank_avg"], row["flying"],
                ).replace("-", "▲").replace("*", "-")

        # --- メモ表示
        resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
        resultdb.row_factory = sqlite3.Row
        rows = resultdb.execute(
            "select * from remarks where thread_ts between ? and ? order by thread_ts,event_ts", (
                first_game.timestamp(),
                last_game.timestamp(),
            )
        )
        for row in rows.fetchall():
            g.logging.trace(dict(row)) # type: ignore
            name = c.member.NameReplace(row["name"], command_option, add_mark = True)
            if name in list(summary_data["name"].unique()):
                msg3 += "\t{}： {} （{}）\n".format(
                    datetime.fromtimestamp(float(row["thread_ts"])).strftime('%Y/%m/%d %H:%M:%S'),
                    row["matter"],
                    name,
                )

        resultdb.close()

    if msg3:
        msg3 = "*【メモ】*\n" + msg3

    return(msg1, msg2, msg3)
