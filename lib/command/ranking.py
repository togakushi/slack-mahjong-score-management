import math
import sqlite3

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def select_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    origin_point = g.config["mahjong"].getint("point", 250) # 配給原点
    return_point = g.config["mahjong"].getint("return", 300) # 返し点

    sql = """
        select
            name as プレイヤー,
            count() as ゲーム数,
            round(sum(point), 1) as 累積ポイント,
            round(avg(point), 1) as 平均ポイント,
            round(sum(rpoint), 1) as 累積素点,
            round(avg(rpoint), 1) as 平均素点,
            round(avg(rpoint) - ?, 1) as 平均収支1,
            round(avg(rpoint) - ?, 1) as 平均収支2,
            round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as トップ率,
            round(cast(count(rank <= 2 or null) as real) / count() * 100, 2) as 連対率,
            round(cast(count(rank <= 3 or null) as real) / count() * 100, 2) as ラス回避率,
            count(rank = 1 or null) as '1位',
            count(rank = 2 or null) as '2位',
            count(rank = 3 or null) as '3位',
            count(rank = 4 or null) as '4位',
            round(avg(rank), 2) as 平均順位,
            count(rpoint < 0 or null) as トビ回数,
            round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as トビ率,
            ifnull(sum(gs_count), 0) as 役満和了,
            round(cast(ifnull(sum(gs_count), 0) as real) / count() * 100,2 ) as 役満和了率,
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then individual_results.name else ? end as name, -- ゲスト有効
                --[unregistered_not_replace] individual_results.name, -- ゲスト無効
                rpoint,
                rank,
                point,
                gs_count
            from
                individual_results
            left outer join
                (select thread_ts, name,count() as gs_count from remarks group by thread_ts, name) as remarks
                on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
            where
                rule_version = ?
                and playtime between ? and ?
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) > 1) -- ゲストあり(2ゲスト戦除外)
                --[guest_skip] and guest = 0 -- ゲストなし
            order by
                playtime desc
            --[recent] limit ? * 4 -- 直近N(縦持ちなので4倍する)
        )
        group by
            name
        having
            count() >= ? -- 規定打数
        order by
            count() desc
    """

    placeholder = [origin_point, return_point, g.guest_name, g.rule_version, starttime, endtime, command_option["stipulated"]]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))

    if target_count != 0:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder.pop(placeholder.index(starttime))
        placeholder.pop(placeholder.index(endtime))
        placeholder += [target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player,
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def slackpost(client, channel, argument, command_option):
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

    command_option : dict
        コマンドオプション
    """

    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    msg1, msg2 = aggregation(argument, command_option)
    res = f.slack_api.post_message(client, channel, msg1)
    if msg2:
        f.slack_api.post_message(client, channel, msg2, res["ts"])


def aggregation(argument, command_option):
    """
    ランキングデータを表示

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1, msg2 : text
        slackにpostする内容
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    # --- データ取得
    ret = d.query_count_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    total_game_count = rows.fetchone()[0]
    command_option["stipulated"] = math.ceil(total_game_count * command_option["stipulated_rate"]) + 1

    ret = select_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    results = {}
    name_list = []
    for row in rows.fetchall():
        results[row["プレイヤー"]] = dict(row)
        name_list.append(c.NameReplace(row["プレイヤー"], command_option, add_mark = True))
        g.logging.trace(f"{row['プレイヤー']}: {results[row['プレイヤー']]}")
    g.logging.info(f"return record: {len(results)}")

    if len(results) == 0: # 結果が0件のとき
        return(f.message.no_hits(ret["starttime"], ret["endtime"]), None)

    padding = c.CountPadding(list(set(name_list)))
    first_game = min([results[name]["first_game"] for name in results.keys()])
    last_game = max([results[name]["last_game"] for name in results.keys()])

    msg1 = "\n*【ランキング】*\n"
    msg1 += f"\t集計範囲：{first_game} ～ {last_game}\n".replace("-", "/")
    msg1 += f"\t集計ゲーム数：{total_game_count}\t(規定数：{command_option['stipulated']} 以上)\n"
    msg1 += f.remarks(command_option)
    msg2 = ""

    # ゲーム参加率
    tmp = {}
    juni = []
    for name in results.keys():
        tmp[name] = results[name]["ゲーム数"]
        juni.append(results[name]["ゲーム数"])
    ranking = sorted(tmp.items(), key = lambda x:x[1], reverse = True)
    juni.sort(reverse = True)
    msg2 += "\n*ゲーム参加率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>6.2%} ({:3d} / {:3d}ゲーム)\n".format(
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
    msg2 += "\n*累積ポイント*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>7.1f}pt ({:2d}ゲーム)\n".format(
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
    msg2 += "\n*平均ポイント*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>5.1f}pt ({:>7.1f}pt / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*平均収支1* (最終素点-配給原点)/ゲーム数\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*平均収支2* (最終素点-返し点)/ゲーム数\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>8.0f}点 ({:>5.0f}点 / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*トップ率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*連対率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*ラス回避率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*トビ率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
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
    msg2 += "\n*平均順位*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        msg2 += "{:3d}： {}{} {:>4.2f} ({:2d}ゲーム)\n".format(
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
    msg2 += "\n*役満和了率*\n"
    for name, val in ranking:
        if juni.index(val) + 1 > command_option["ranked"]:
            break
        pname = c.NameReplace(name, command_option, add_mark = True)
        if results[name]["役満和了"] == 0:
            continue
        msg2 += "{:3d}： {}{} {:>6.2f}% ({:2d} / {:2d}ゲーム)\n".format(
            juni.index(val) + 1, pname, " " * (padding - f.len_count(pname)),
            val, results[name]["役満和了"], results[name]["ゲーム数"],
        )

    return(msg1, msg2)
