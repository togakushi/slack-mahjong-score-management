import math
import sqlite3

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def help_message():
    ranking_option = f.configure.command_option_initialization("ranking")

    msg = [
        "*成績ランキングヘルプ*",
        f"\t呼び出しキーワード： {g.commandword['ranking']}",
        f"\t検索範囲デフォルト： {ranking_option['aggregation_range'][0]}",
        f"\t規定打数デフォルト： 全体ゲーム数 × {ranking_option['stipulated_rate']} ＋ 1",
        f"\t出力制限デフォルト： 上位 {ranking_option['ranked']} 名",
        "\n*専用オプション*",
        "\t・トップ / 上位： 出力制限人数の変更",
    ]
    return("\n".join(msg))


def slackpost(client, channel, argument):
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

    # ヘルプ表示
    if command_option["help"]:
        return(help_message())

    msg1, msg2 = aggregation(argument, command_option)
    res = f.slack_api.post_message(client, channel, msg1)
    if msg2:
        # ブロック単位で分割ポスト
        key_list = list(msg2.keys())
        msg = msg2[key_list[0]]
        for i in key_list[1:]:
            if len((msg + msg2[i]).splitlines()) < 95: # 95行を超える直前までまとめる
                msg += msg2[i]
            else:
                f.slack_api.post_message(client, channel, msg, res["ts"])
                msg = msg2[i]
        else:
            f.slack_api.post_message(client, channel, msg, res["ts"])


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

    # --- データ取得
    ret = d.query_count_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    total_game_count = rows.fetchone()[0]
    if command_option["stipulated"] == 0:
        command_option["stipulated"] = math.ceil(total_game_count * command_option["stipulated_rate"]) + 1

    ret = d.query_get_personal_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    results = {}
    name_list = []
    for row in rows.fetchall():
        results[row["プレイヤー"]] = dict(row)
        name_list.append(c.NameReplace(row["プレイヤー"], command_option, add_mark = True))
        g.logging.trace(f"{row['プレイヤー']}: {results[row['プレイヤー']]}")
    g.logging.info(f"return record: {len(results)}")

    if len(results) == 0: # 結果が0件のとき
        return(f.message.no_hits(argument, command_option), None)

    padding = c.CountPadding(list(set(name_list)))
    first_game = min([results[name]["first_game"] for name in results.keys()])
    last_game = max([results[name]["last_game"] for name in results.keys()])

    msg1 = "\n*【ランキング】*\n"
    msg1 += f"\t集計期間：{first_game} ～ {last_game}\n".replace("-", "/")
    msg1 += f"\t集計ゲーム数：{total_game_count}\t(規定数：{command_option['stipulated']} 以上)\n"
    msg1 += f.remarks(command_option)
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
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["ゲーム数"]
        juni.append(results[name]["ゲーム数"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["ゲーム参加率"] += "{:3d}： {}{} {:>6.2%} ({:3d} / {:3d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val / total_game_count, val, total_game_count,
        )

    # 累積ポイント
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["累積ポイント"]
        juni.append(results[name]["累積ポイント"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["累積ポイント"] += "{:3d}： {}{} {:>7.1f}pt ({:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均ポイント
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["平均ポイント"]
        juni.append(results[name]["平均ポイント"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["平均ポイント"] += "{:3d}： {}{} {:>5.1f}pt ({:>7.1f}pt / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["累積ポイント"], results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均収支1
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["平均収支1"]
        juni.append(results[name]["平均収支1"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["平均収支1"] += "{:3d}： {}{} {:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val * 100, results[name]["平均素点"] * 100, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # 平均収支2
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["平均収支2"]
        juni.append(results[name]["平均収支2"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["平均収支2"] += "{:3d}： {}{} {:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val * 100, results[name]["平均素点"] * 100, results[name]["ゲーム数"],
        ).replace("-", "▲")

    # トップ率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["トップ率"]
        juni.append(results[name]["トップ率"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["トップ率"] += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["1位"], results[name]["ゲーム数"],
        )

    # 連対率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["連対率"]
        juni.append(results[name]["連対率"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["連対率"] += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["1位"] + results[name]["2位"], results[name]["ゲーム数"],
        )

    # ラス回避率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["ラス回避率"]
        juni.append(results[name]["ラス回避率"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["ラス回避率"] += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["1位"] + results[name]["2位"] + results[name]["3位"], results[name]["ゲーム数"],
        )

    # トビ率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["トビ率"]
        juni.append(results[name]["トビ率"])
    ranking = sorted(tmp.items(), key = lambda x:x[1])
    juni.sort()
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["トビ率"] += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["トビ回数"], results[name]["ゲーム数"],
        )

    # 平均順位
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["平均順位"]
        juni.append(results[name]["平均順位"])
    ranking = sorted(tmp.items(), key = lambda x:x[1])
    juni.sort()
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2["平均順位"] += "{:3d}： {}{} {:>4.2f} ({:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["ゲーム数"],
        )

    # 役満和了率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["役満和了率"]
        juni.append(results[name]["役満和了率"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        if results[name]["役満和了"] != 0:
            msg2["役満和了率"] += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
                juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
                val, results[name]["役満和了"], results[name]["ゲーム数"],
            )
    if msg2["役満和了率"].strip().count("\n") == 0: # 対象者がいなければ削除
        msg2.pop("役満和了率")

    return(msg1, msg2)
