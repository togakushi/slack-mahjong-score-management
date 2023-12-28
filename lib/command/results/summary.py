import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def select_game(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        --[recent] select * from (
        select
            name,
            count() as count,
            round(sum(point), 1) as pt_total,
            round(avg(point), 1) as pt_avg,
            count(rank = 1 or null) as "1st",
            count(rank = 2 or null) as "2nd",
            count(rank = 3 or null) as "3rd",
            count(rank = 4 or null) as "4th",
            round(avg(rank), 2) as rank_avg,
            count(rpoint < 0 or null) as flying,
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select
                playtime,
                --[unregistered_replace] case when guest = 0 then name else ? end as name, -- ゲスト有効
                --[unregistered_not_replace] name, -- ゲスト無効
                rpoint, rank, point, guest, rule_version
            from
                individual_results
            where
                rule_version = ?
                and playtime between ? and ? -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[guest_skip] and guest = 0 -- ゲストなし
                --[target_player] and name in (<<target_player>>) -- 対象プレイヤー
            order by
                playtime desc
            --[recent] limit ?
        )
        group by
            name
        order by
            pt_total desc
        --[recent] )
    """

    placeholder = [g.guest_name, g.rule_version, starttime, endtime]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
        placeholder.pop(placeholder.index(g.guest_name))
    if target_player:
        sql = sql.replace("--[target_player] ", "")
        p = []
        for i in target_player:
            p.append("?")
            placeholder.append(i)
        sql = sql.replace("<<target_player>>", ",".join([i for i in p]))

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

def count_game(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        --[recent] select * from (
        select
            count() as count
        from (
            select
                playtime
            from
                individual_results
            where
                rule_version = ?
                and playtime between ? and ? -- 検索範囲
                --[guest_not_skip] and playtime not in (select playtime from individual_results group by playtime having sum(guest) >= 2) -- ゲストあり
                --[target_player] and name in (<<target_player>>) -- 対象プレイヤー
            group by
                playtime
            order by
                playtime desc
            --[recent] limit ?
        )
        --[recent] )
    """

    placeholder = [g.rule_version, starttime, endtime]

    if command_option["unregistered_replace"]:
        sql = sql.replace("--[unregistered_replace] ", "")
        if command_option["guest_skip"]:
            sql = sql.replace("--[guest_not_skip] ", "")
        else:
            sql = sql.replace("--[guest_skip] ", "")
    else:
        sql = sql.replace("--[unregistered_not_replace] ", "")
    if target_player:
        sql = sql.replace("--[target_player] ", "")
        p = []
        for i in target_player:
            p.append("?")
            placeholder.append(i)
        sql = sql.replace("<<target_player>>", ",".join([i for i in p]))

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

    ret = count_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    gamecount = rows.fetchone()[0]

    ret = select_game(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])

    # ---
    results = {}
    name_list = []
    for row in rows.fetchall():
        name_list.append(c.NameReplace(row["name"], command_option, add_mark = True))
        results[row["name"]] = {
            "count": row["count"], "first_game": row["first_game"], "last_game": row["last_game"],
            "pt_total": row["pt_total"], "pt_avg": row["pt_avg"],
            "1st": row["1st"], "2nd": row["2nd"], "3rd": row["3rd"], "4th": row["4th"],
            "rank_avg": row["rank_avg"], "flying": row["flying"],
        }
        g.logging.trace(f"{row['name']}: {results[row['name']]}")
    g.logging.info(f"return record: {len(results)}")

    ### 表示 ###
    if len(results) == 0: # 結果が0件のとき
        return(None, f.message.no_hits(ret["starttime"], ret["endtime"]), None)

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
        msg2 += f"\t総ゲーム数：{gamecount} 回"
    else:
        msg2 += f"\tゲーム数：{gamecount} 回"

    if g.config["mahjong"].getboolean("ignore_flying", False):
        msg2 += "\n"
    else:
        msg2 += " / トバされた人（延べ）： {} 人\n".format(
            sum([results[name]["flying"] for name in results.keys()]),
        )
    msg2 += f.remarks(command_option)

    # --- 集計結果
    padding = c.CountPadding(list(set(name_list)))
    if command_option["score_comparisons"]: # 差分表示
        header = "## {} {}： 累積    / 点差 ##\n".format(
            "名前", " " * (padding - f.translation.len_count("名前") - 4),
        )
        previous_point = None
        for name in results.keys():
            pname = c.NameReplace(name, command_option, add_mark = True)
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
            pname = c.NameReplace(name, command_option, add_mark = True)
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
                datetime.fromisoformat(last_game).timestamp(),
            )
        )
        for row in rows.fetchall():
            name = c.NameReplace(row["name"], command_option)
            if name in name_list:
                msg3 += "\t{}： {} （{}）\n".format(
                    datetime.fromtimestamp(float(row["thread_ts"])).strftime('%Y/%m/%d %H:%M:%S'),
                    row["matter"],
                    name,
                )

    if msg3:
        msg3 = "*【メモ】*\n" + msg3

    return(header + msg1, msg2, msg3)
