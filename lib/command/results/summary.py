import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
import lib.database as d
import lib.command.results._query as query
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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = d._query.query_count_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    total_game_count = rows.fetchone()[0]

    ret = query.select_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # ---
    results = {}
    name_list = []
    for row in rows.fetchall():
        results[row["name"]] = dict(row)
        name_list.append(c.member.NameReplace(row["name"], command_option, add_mark = True))
        g.logging.trace(f"{row['name']}: {results[row['name']]}") # type: ignore
    g.logging.info(f"return record: {len(results)}")

    ### 表示 ###
    if len(results) == 0: # 結果が0件のとき
        return(None, f.message.no_hits(argument, command_option), None)

    msg1 = ""
    msg2 = "*【成績サマリ】*\n"
    msg3 = ""
    first_game = min([results[name]["first_game"] for name in results.keys()])
    last_game = max([results[name]["last_game"] for name in results.keys()])

    # --- 情報ヘッダ
    if ret["target_count"] == 0: # 直近指定がない場合は検索範囲を付ける
        msg2 += "\t検索範囲：{} ～ {}\n".format(
            ret["starttime"].strftime('%Y/%m/%d %H:%M'), ret["endtime"].strftime('%Y/%m/%d %H:%M'),
        )
    msg2 += "\t最初のゲーム：{}\n\t最後のゲーム：{}\n".format(
        first_game.replace("-", "/"), last_game.replace("-", "/"),
    )
    if ret["target_player"]:
        msg2 += f"\t総ゲーム数：{total_game_count} 回"
    else:
        msg2 += f"\tゲーム数：{total_game_count} 回"

    if g.config["mahjong"].getboolean("ignore_flying", False):
        msg2 += "\n"
    else:
        msg2 += " / トバされた人（延べ）： {} 人\n".format(
            sum([results[name]["flying"] for name in results.keys()]),
        )
    msg2 += f.message.remarks(command_option)

    # --- 集計結果
    padding = c.member.CountPadding(list(set(name_list)))
    if command_option["score_comparisons"]: # 差分表示
        header = "## {} {}： 累積    / 点差 ##\n".format(
            "名前", " " * (padding - f.translation.len_count("名前") - 4),
        )
        previous_point = None
        for name in results.keys():
            pname = c.member.NameReplace(name, command_option, add_mark = True)
            if previous_point == None:
                msg1 += "{} {}： {:>+6.1f} / *****\n".format(
                    pname, " " * (padding - f.translation.len_count(pname)),
                    results[name]["pt_total"],
                ).replace("-", "▲").replace("*", "-")
            else:
                msg1 += "{} {}： {:>+6.1f} / {:>5.1f}\n".format(
                    pname, " " * (padding - f.translation.len_count(pname)),
                    results[name]["pt_total"],
                    previous_point - results[name]["pt_total"],
                ).replace("-", "▲")
            previous_point = results[name]["pt_total"]
    else: # 通常表示
        header = "## {} {} : 累積 (平均) / 順位分布 (平均)".format(
            "名前", " " * (padding - f.translation.len_count("名前") - 4),
        )
        if g.config["mahjong"].getboolean("ignore_flying", False):
            header += " ##\n"
        else:
            header +=" / トビ ##\n"
        for name in results.keys():
            pname = c.member.NameReplace(name, command_option, add_mark = True)
            msg1 += "{} {}： {:>+6.1f} ({:>+5.1f})".format(
                pname, " " * (padding - f.translation.len_count(pname)),
                results[name]["pt_total"], results[name]["pt_avg"],
            ).replace("-", "▲")
            msg1 += " / {}-{}-{}-{} ({:1.2f})".format(
                results[name]["1st"], results[name]["2nd"],
                results[name]["3rd"], results[name]["4th"],
                results[name]["rank_avg"],
            )
            if g.config["mahjong"].getboolean("ignore_flying", False):
                msg1 += "\n"
            else:
                msg1 += f" / {results[name]['flying']}\n"

        # --- メモ表示
        rows = resultdb.execute(
            "select * from remarks where thread_ts between ? and ? order by thread_ts,event_ts", (
                datetime.fromisoformat(first_game).timestamp(),
                max([results[i]["max_ts"] for i in results.keys()]),
            )
        )
        for row in rows.fetchall():
            g.logging.trace(dict(row)) # type: ignore
            name = c.member.NameReplace(row["name"], command_option, add_mark = True)
            if name in name_list:
                msg3 += "\t{}： {} （{}）\n".format(
                    datetime.fromtimestamp(float(row["thread_ts"])).strftime('%Y/%m/%d %H:%M:%S'),
                    row["matter"],
                    name,
                )

    if msg3:
        msg3 = "*【メモ】*\n" + msg3

    return(header + msg1, msg2, msg3)
