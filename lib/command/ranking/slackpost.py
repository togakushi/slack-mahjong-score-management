import math
import sqlite3

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def main(client, channel, argument):
    """
    ランキングをslackにpostする

    Parameters
    ----------
    client : obj

    channel : str
        post先のチャンネルID or ユーザーID

    argument : list
        slackから受け取った引数
        解析対象のプレイヤー、検索範囲などが指定される
    """

    command_option = f.configure.command_option_initialization("ranking")
    _, _, _, command_option = f.common.argument_analysis(argument, command_option)

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    msg1, msg2 = aggregation(argument, command_option)
    res = f.slack_api.post_message(client, channel, msg1)
    if msg2:
        f.slack_api.post_multi_message(client, channel, msg2, res["ts"])


def aggregation(argument, command_option):
    """
    ランキングデータを生成

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        ランキングの集計情報

    msg2 : dict
        各ランキングの情報
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    cur = resultdb.cursor()

    # --- データ取得
    total_game_count = d.common.game_count(argument, command_option, cur)
    if command_option["stipulated"] == 0:
        command_option["stipulated"] = math.ceil(total_game_count * command_option["stipulated_rate"]) + 1

    results = d._query.query_get_personal_data(argument, command_option, cur)
    if len(results) == 0: # 結果が0件のとき
        return(f.message.no_hits(argument, command_option), None)

    padding = c.member.CountPadding(list(set(results.keys())))
    first_game = min([results[name]["first_game"] for name in results.keys()])
    last_game = max([results[name]["last_game"] for name in results.keys()])

    msg1 = "\n*【ランキング】*\n"
    msg1 += f"\t集計範囲：{first_game} ～ {last_game}\n".replace("-", "/")
    msg1 += f"\t集計ゲーム数：{total_game_count}\t(規定数：{command_option['stipulated']} 以上)\n"
    msg1 += f.message.remarks(command_option)
    msg2 = {
        "ゲーム参加率": "\n*ゲーム参加率*\n",
        "累積ポイント": "\n*累積ポイント*\n",
        "平均ポイント": "\n*平均ポイント*\n",
        "平均収支1": "\n*平均収支1* (最終素点-配給原点)/ゲーム数\n",
        "平均収支2": "\n*平均収支2* (最終素点-返し点)/ゲーム数\n",
        "トップ率": "\n*トップ率*\n",
        "連対率": "\n*連対率*\n",
        "ラス回避率": "\n*ラス回避率*\n",
        "トビ率": "\n*トビ率*\n",
        "平均順位": "\n*平均順位*\n",
        "役満和了率": "\n*役満和了率*\n",
    }

    # ゲーム参加率
    ranking_data = ranking_sort(results, "ゲーム数")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["ゲーム参加率"] += "{:3d}： {}{} \t{:>6.2%} ({:3d} / {:3d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val / total_game_count, val, total_game_count,
        )

    # 累積ポイント
    ranking_data = ranking_sort(results, "累積ポイント")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["累積ポイント"] += "{:3d}： {}{} \t{:>7.1f}pt ({:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均ポイント
    ranking_data = ranking_sort(results, "平均ポイント")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["平均ポイント"] += "{:3d}： {}{} \t{:>5.1f}pt ({:>7.1f}pt / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["累積ポイント"], results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均収支1
    ranking_data = ranking_sort(results, "平均収支1")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["平均収支1"] += "{:3d}： {}{} \t{:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val * 100, results[name]["平均素点"] * 100, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均収支2
    ranking_data = ranking_sort(results, "平均収支2")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["平均収支2"] += "{:3d}： {}{} \t{:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val * 100, results[name]["平均素点"] * 100, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # トップ率
    ranking_data = ranking_sort(results, "トップ率")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["トップ率"] += "{:3d}： {}{} \t{:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["1位"], results[name]["ゲーム数"],
        )

    # 連対率
    ranking_data = ranking_sort(results, "連対率")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["連対率"] += "{:3d}： {}{} \t{:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["1位"] + results[name]["2位"], results[name]["ゲーム数"],
        )

    # ラス回避率
    ranking_data = ranking_sort(results, "ラス回避率")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["ラス回避率"] += "{:3d}： {}{} \t{:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["1位"] + results[name]["2位"] + results[name]["3位"], results[name]["ゲーム数"],
        )

    # トビ率
    ranking_data = ranking_sort(results, "トビ率", False)
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["トビ率"] += "{:3d}： {}{} \t{:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["トビ回数"], results[name]["ゲーム数"],
        )

    # 平均順位
    ranking_data = ranking_sort(results, "平均順位", False)
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        msg2["平均順位"] += "{:3d}： {}{} \t{:>4.2f} ({:2d}ゲーム)\n".format(
            ranking_data.index((name, val)) + 1,
            pname, " " * (padding - f.common.len_count(pname)),
            val, results[name]["ゲーム数"],
        )

    # 役満和了率
    ranking_data = ranking_sort(results, "役満和了率")
    for name, val in ranking_data:
        if ranking_data.index((name, val)) + 1 > command_option["ranked"]:
            break
        pname = c.member.NameReplace(name, command_option, add_mark = True)
        if results[name]["役満和了"] != 0:
            msg2["役満和了率"] += "{:3d}： {}{} \t{:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
                ranking_data.index((name, val)) + 1,
                pname, " " * (padding - f.common.len_count(pname)),
                val, results[name]["役満和了"], results[name]["ゲーム数"],
            )
    if msg2["役満和了率"].strip().count("\n") == 0: # 対象者がいなければ項目を削除
        msg2.pop("役満和了率")

    return(msg1, msg2)


def ranking_sort(data, keyword, reverse = True):
    """
    指定項目のデータを順位順で返す

    Parameters
    ----------
    data : dict
        対象データ

    keyword : str
        対象項目

    reverse : bool
        昇順/降順

    Returns
    -------
    ranking_data : list
        並べ変えられた結果(名前, 値のタプル)
    """

    tmp_data = {}
    for name in data.keys():
        tmp_data[name] = data[name][keyword]

    ranking_data = sorted(tmp_data.items(), key = lambda x:x[1], reverse = reverse)
    g.logging.trace(f"{keyword}: {ranking_data}") # type: ignore

    return(ranking_data)
