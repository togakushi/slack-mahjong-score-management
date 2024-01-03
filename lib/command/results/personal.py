import sqlite3

import lib.command as c
import lib.function as f
import lib.command.results._query as query
from lib.function import global_value as g


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

    ret = query.select_personal_data(argument, command_option)
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
    msg1 = "*【個人成績】*\n\tプレイヤー名： {} {}\n".format(
        c.NameReplace(data["name"], command_option, add_mark = True),
        badge_degree,
    )
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
        ret = query.select_game_results(argument, command_option)
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
            ret = query.select_versus_matrix(argument, command_option)
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
