import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g

def select_personal_data(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            individual_results.name,
            count() as game,
            count(point > 0 or null) as win, count(point < 0 or null) as lose, count(point = 0 or null) as draw,
            round(sum(point), 1) as pt_total, round(avg(point), 1) as pt_avg,
            count(rank = 1 or null) as '1st', round(cast(count(rank = 1 or null) as real) / count() * 100, 2) as '1st%',
            count(rank = 2 or null) as '2nd', round(cast(count(rank = 2 or null) as real) / count() * 100, 2) as '2nd%',
            count(rank = 3 or null) as '3rd', round(cast(count(rank = 3 or null) as real) / count() * 100, 2) as '3rd%',
            count(rank = 4 or null) as '4th', round(cast(count(rank = 4 or null) AS real) / count() * 100, 2) as '4th%',
            round(avg(rank), 2) as rank_avg,
            count(matter) as gs, round(cast(count(matter) as REAL) / count() * 100, 2) as 'gs%',
            count(rpoint < 0 or null) as flying, round(cast(count(rpoint < 0 or null) as real) / count() * 100, 2) as 'flying%',
            -- 座席順位分布
            count(seat = 1 and rank = 1 or null) as 's1-1st',
            count(seat = 1 and rank = 2 or null) as 's1-2nd',
            count(seat = 1 and rank = 3 or null) as 's1-3rd',
            count(seat = 1 and rank = 4 or null) as 's1-4th',
            round(avg(case when seat = 1 then rank end), 2) as 's1-rank_avg',
            count(seat = 1 and matter != '' or null) as 's1-gs',
            count(seat = 1 and rpoint < 0 or null) as 's1-flying',
            count(seat = 2 and rank = 1 or null) as 's2-1st',
            count(seat = 2 and rank = 2 or null) as 's2-2nd',
            count(seat = 2 and rank = 3 or null) as 's2-3rd',
            count(seat = 2 and rank = 4 or null) as 's2-4th',
            round(avg(case when seat = 2 then rank end), 2) as 's2-rank_avg',
            count(seat = 2 and matter != '' or null) as 's2-gs',
            count(seat = 2 and rpoint < 0 or null) as 's2-flying',
            count(seat = 3 and rank = 1 or null) as 's3-1st',
            count(seat = 3 and rank = 2 or null) as 's3-2nd',
            count(seat = 3 and rank = 3 or null) as 's3-3rd',
            count(seat = 3 and rank = 4 or null) as 's3-4th',
            round(avg(case when seat = 3 then rank end), 2) as 's3-rank_avg',
            count(seat = 3 and matter != '' or null) as 's3-gs',
            count(seat = 3 and rpoint < 0 or null) as 's3-flying',
            count(seat = 4 and rank = 1 or null) as 's4-1st',
            count(seat = 4 and rank = 2 or null) as 's4-2nd',
            count(seat = 4 and rank = 3 or null) as 's4-3rd',
            count(seat = 4 and rank = 4 or null) as 's4-4th',
            round(avg(case when seat = 4 then rank end), 2) as 's4-rank_avg',
            count(seat = 4 and matter != '' or null) as 's4-gs',
            count(seat = 4 and rpoint < 0 or null) as 's4-flying',
            min(playtime) as first_game,
            max(playtime) as last_game
        from (
            select * from individual_results
            where individual_results.name = ?
            order by playtime desc
            --[recent] limit ?
        ) individual_results
        left outer join
            remarks on individual_results.ts = remarks.thread_ts and individual_results.name = remarks.name
        where
            rule_version = ?
            and playtime between ? and ?
        group by
            individual_results.name
    """

    if target_count == 0:
        placeholder = [target_player[0], g.rule_version, starttime, endtime]
    else:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [target_player[0], target_count, g.rule_version]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_game_results(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select * from (
            select
                playtime, ts,
                p1_guest + p2_guest + p3_guest + p4_guest as guest_count,
                p1_name, p1_rpoint * 100 as p1_rpoint, p1_rank, p1_point,
                p2_name, p2_rpoint * 100 as p2_rpoint, p2_rank, p2_point,
                p3_name, p3_rpoint * 100 as p3_rpoint, p3_rank, p3_point,
                p4_name, p4_rpoint * 100 as p4_rpoint, p4_rank, p4_point
            from
                game_results
            where
                rule_version = ?
                and playtime between ? and ?
                and ? in (p1_name, p2_name, p3_name, p4_name)
            order by
                playtime desc
            --[recent] limit ?
        )
        order by
            playtime
        """

    if target_count == 0:
        placeholder = [g.rule_version, starttime, endtime, target_player[0]]
    else:
        sql = sql.replace("and playtime between", "-- and playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, target_player[0], target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def select_versus_matrix(argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    sql = """
        select
            my_name, vs_name,
            count() as game,
            count(my_rank < vs_rank or null) as win,
            count(my_rank > vs_rank or null) as lose,
            round(cast(count(my_rank < vs_rank or null) AS real) / count() * 100, 2) as 'win%'
        from (
            select
                my.name as my_name,
                my.rank as my_rank,
                vs.name as vs_name,
                vs.rank as vs_rank
            from
                individual_results my
            inner join
                individual_results vs
                    on (my.playtime = vs.playtime and my.name != vs.name)
            where
                my.rule_version = ?
                and my.playtime between ? and ?
                and my.name = ?
            order by
                my.playtime desc
            --[recent] limit ?
        )
        group by
            my_name, vs_name
        order by
            game desc
    """

    if target_count == 0:
        placeholder = [g.rule_version, starttime, endtime, target_player[0]]
    else:
        sql = sql.replace("and my.playtime between", "-- and my.playtime between")
        sql = sql.replace("--[recent] ", "")
        placeholder = [g.rule_version, target_player[0], target_count]

    g.logging.trace(f"sql: {sql}")
    g.logging.trace(f"placeholder: {placeholder}")

    return {
        "target_days": target_days,
        "target_player": target_player[0],
        "target_count": target_count,
        "starttime": starttime,
        "endtime": endtime,
        "sql": sql,
        "placeholder": placeholder,
    }


def aggregation(argument, command_option):
    """
    個人成績を集計して返す

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg : text
        slackにpostするデータ

    msg2 : dict
        slackにpostするデータ(スレッドに返す)
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    ret = select_personal_data(argument, command_option)
    rows = resultdb.execute(ret["sql"], ret["placeholder"])
    data = rows.fetchone()

    if data:
        g.logging.trace(dict(data))
    else:
        data = {
            "name": ret["target_player"],
            "game": 0, "win": 0, "lose": 0, "draw": 0,
        }

    ### 表示オプション ###
    badge_degree = ""
    if g.config["degree"].getboolean("display", False):
        degree_badge = g.config.get("degree", "badge").split(",")
        degree_counter = [x for x in map(int, g.config.get("degree", "counter").split(","))]
        for i in range(len(degree_counter)):
            if data["game"] >= degree_counter[i]:
                badge_degree = degree_badge[i]

    badge_status = ""
    if g.config["status"].getboolean("display", False):
        status_badge = g.config.get("status", "badge").split(",")
        status_step = g.config.getfloat("status", "step")
        if data["game"] == 0:
            index = 0
        else:
            winper = data["win"] / data["game"] * 100
            index = 3
            for i in (1, 2, 3):
                if winper <= 50 - status_step * i:
                    index = 4 - i
                if winper >= 50 + status_step * i:
                    index = 2 + i
        badge_status = status_badge[index]

    ### 表示内容 ###
    msg1 = f"*【個人成績】*\n\tプレイヤー名： {data['name']} {badge_degree}\n"
    msg2 = {}
    msg2["座席"] = "*【座席データ】*\n"
    if command_option["guest_skip"]:
        msg2["戦績"] = "*【戦績】*\n"
    else:
        if command_option["verbose"]:
            msg2["戦績"] = f"*【戦績】*\n"
        else:
            msg2["戦績"] = f"*【戦績】* （{g.guest_mark.strip()}：2ゲスト戦）\n"
    msg2["対戦"] = "*【対戦結果】*\n"

    # 成績
    if data["game"] == 0:
        msg1 += f"\t対戦数：{data['game']} 戦 ({data['win']} 勝 {data['lose']} 敗 {data['draw']} 分) {badge_status}\n"
        msg2.clear()
    else:
        msg1 += "\t集計範囲：{} ～ {}\n".format(
            data["first_game"].replace("-", "/"), data["last_game"].replace("-", "/"),
        )
        msg1 += f"\t対戦数：{data['game']} 戦 ({data['win']} 勝 {data['lose']} 敗 {data['draw']} 分) {badge_status}\n"
        msg1 += "\t累積ポイント： {:+.1f}\n".format(data["pt_total"]).replace("-", "▲")
        msg1 += "\t平均ポイント： {:+.1f}\n".format(data["pt_avg"]).replace("-", "▲")
        msg1 += "\t平均順位： {:1.2f}\n".format(data["rank_avg"])
        msg1 += "\t1位： {:2} 回 ({:.2f}%)\n".format(data["1st"], data["1st%"])
        msg1 += "\t2位： {:2} 回 ({:.2f}%)\n".format(data["2nd"], data["2nd%"])
        msg1 += "\t3位： {:2} 回 ({:.2f}%)\n".format(data["3rd"], data["3rd%"])
        msg1 += "\t4位： {:2} 回 ({:.2f}%)\n".format(data["4th"], data["4th%"])
        if not g.config["mahjong"].getboolean("ignore_flying", False):
            msg1 += "\tトビ： {} 回 ({:.2f}%)\n".format(data["flying"], data["flying%"])
        msg1 += "\t役満： {:2} 回 ({:.2f}%)\n".format(data["gs"], data["gs%"])
        msg1 += "\n" + f.remarks(command_option)

        # 座席
        msg2["座席"] += "\t# 席：順位分布(平順) / トビ / 役満 #\n"
        for n, s in [("東家", "s1"), ("南家", "s2"), ("西家", "s3"), ("北家", "s4")]:
            if data[f"{s}-rank_avg"]:
                msg2["座席"] += "\t{}： {}-{}-{}-{} ({:1.2f})".format(
                    n, data[f"{s}-1st"], data[f"{s}-2nd"], data[f"{s}-3rd"], data[f"{s}-4th"], data[f"{s}-rank_avg"]
                )
            else:
                msg2["座席"] += f"\t{n}： 0-0-0-0 (-.--)"
            if g.config["mahjong"].getboolean("ignore_flying", False):
                msg2["座席"] = msg2["座席"].replace("/ トビ /", "/")
                msg2["座席"] += " / {} 回\n".format(
                    data[f"{s}-gs"] if data[f"{s}-rank_avg"] else "--",
                )
            else:
                msg2["座席"] += " / {} 回 / {} 回\n".format(
                    data[f"{s}-flying"] if data[f"{s}-rank_avg"] else "--",
                    data[f"{s}-gs"] if data[f"{s}-rank_avg"] else "--",
                )

        # 戦績
        ret = select_game_results(argument, command_option)
        rows = resultdb.execute(ret["sql"], ret["placeholder"])

        # 結果保存
        results = {}
        for row in rows.fetchall():
            results[row["playtime"]] = dict(row)

        # パディング計算
        name_list = []
        timestamp = []
        for i in results.keys():
            timestamp.append(results[i]["ts"])
            for p in ("p1", "p2", "p3", "p4"):
                name_list.append(c.NameReplace(results[i][f"{p}_name"], command_option, add_mark = True))
        padding = c.CountPadding(list(set(name_list)))

        # 戦績表示
        if command_option["game_results"]:
            rows = resultdb.execute(
                "select * from remarks where thread_ts between ? and ?", (min(timestamp), max(timestamp))
            )
            game_remarks = {}
            for row in rows.fetchall():
                if not row["name"] in game_remarks:
                    game_remarks[row["name"]] = {}
                if not row["thread_ts"] in game_remarks[row["name"]]:
                    game_remarks[row["name"]][row["thread_ts"]] = []
                game_remarks[row["name"]][row["thread_ts"]].append(row["matter"])

            for i in results.keys():
                if command_option["verbose"]:
                    msg2["戦績"] += "{} {}\n".format(
                        results[i]["playtime"].replace("-", "/"),
                        "(2ゲスト戦)" if results[i]["guest_count"] >= 2 else "",
                    )
                    for n, p in [("東家", "p1"), ("南家", "p2"), ("西家", "p3"), ("北家", "p4")]:
                        matter = ""
                        name = results[i][f"{p}_name"]
                        if name in game_remarks:
                            if results[i]["ts"] in game_remarks[name]:
                                matter = ",".join(game_remarks[name][results[i]["ts"]])
                        pname = c.NameReplace(results[i][f"{p}_name"], command_option, add_mark = True)
                        msg2["戦績"] += "\t{}： {}{} / {}位 {:>7}点 ({}pt) {}\n".format(
                            n, pname, " " * (padding - f.translation.len_count(pname)),
                            results[i][f"{p}_rank"], results[i][f"{p}_rpoint"], results[i][f"{p}_point"], matter,
                        )
                else:
                    matter = ""
                    if data["name"] in game_remarks:
                        if results[i]["ts"] in game_remarks[data["name"]]:
                            matter = ",".join(game_remarks[data["name"]][results[i]["ts"]])
                    seat = [results[i]["p1_name"], results[i]["p2_name"], results[i]["p3_name"], results[i]["p4_name"]].index(data["name"]) + 1
                    msg2["戦績"] += "{}： {}位 {:>7}点 ({:>+5.1f}pt){} {}\n".format(
                        results[i]["playtime"].replace("-", "/"),
                        results[i][f"p{seat}_rank"],
                        results[i][f"p{seat}_rpoint"],
                        results[i][f"p{seat}_point"],
                        g.guest_mark if results[i]["guest_count"] >= 2 else "",
                        matter,
                ).replace("-", "▲")
        else:
            msg2.pop("戦績")

        # 対戦結果
        if command_option["versus_matrix"]:
            ret = select_versus_matrix(argument, command_option)
            rows = resultdb.execute(ret["sql"], ret["placeholder"])

            msg2["対戦"] += "\n```\n"
            for row in rows.fetchall():
                pname = c.NameReplace(row["vs_name"], command_option, add_mark = True)
                msg2["対戦"] += "{}{}：{:3}戦{:3}勝{:3}敗 ({:>6.2f}%)\n".format(
                    pname, " " * (padding - f.translation.len_count(pname)),
                    row["game"], row["win"], row["lose"], row["win%"]
                )
            msg2["対戦"] += "```"
        else:
            msg2.pop("対戦")

    resultdb.close()
    return(msg1.strip(), msg2)
