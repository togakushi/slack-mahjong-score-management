import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def details(starttime, endtime, target_player, target_count, command_option):
    """
    個人成績を集計して返す

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    target_count: int
        集計するゲーム数

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
    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    results = f.search.game_select(starttime, endtime, target_player, target_count, command_option)
    target_player = [c.NameReplace(name, command_option, add_mark = True) for name in target_player] # ゲストマーク付きリストに更新
    g.logging.info(f"target_player(update):  {target_player}")

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    padding = c.CountPadding(results)
    msg1 = "*【個人成績】*\n"
    msg2 = {}
    msg2["座席"] = "*【座席順位分布】*\n"
    if command_option["guest_skip"]:
        msg2["戦績"] = "*【戦績】*\n"
    else:
        msg2["戦績"] = f"*【戦績】* （{g.guest_mark.strip()}：2ゲスト戦）\n"
    msg2["対戦"] = "*【対戦結果】*\n"

    point = 0
    count_rank = [0, 0, 0, 0]
    count_tobi = 0
    count_win = 0
    count_lose = 0
    count_draw = 0
    count_gs = 0 # 役満(Grand Slum)
    versus_matrix = {}
    seat_rank = {
        "東家": [0, 0, 0, 0],
        "南家": [0, 0, 0, 0],
        "西家": [0, 0, 0, 0],
        "北家": [0, 0, 0, 0],
    }
    seat_tobi = [0, 0, 0, 0]

    ### 集計 ###
    for i in results.keys():
        myrank = None
        if [results[i][x]["name"] for x in g.wind[0:4]].count(g.guest_name) >= 2:
            gg_flag = " " + g.guest_mark
        else:
            gg_flag = ""

        tmp_msg1 = results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S") + gg_flag + "\n"
        tmp_msg2 = ""

        # 戦績
        for wind in g.wind[0:4]:
            rows = resultdb.execute(
                "select matter from remarks where thread_ts=? and name=?",
                (str(results[i]["日付"].timestamp()), results[i][wind]["name"])
            )
            game_remarks = [row["matter"] for row in rows.fetchall()]

            tmp_msg1 += "\t{}： {}{} / {}位 {:>5}00点 ({}p) {}\n".format(
                wind, results[i][wind]["name"],
                " " * (padding - f.translation.len_count(results[i][wind]["name"])),
                results[i][wind]["rank"],
                eval(str(results[i][wind]["rpoint"])),
                results[i][wind]["point"],
                ",".join(game_remarks),
            ).replace("-", "▲")

            if target_player[0] == results[i][wind]["name"]:
                myrank = results[i][wind]["rank"]
                count_rank[results[i][wind]["rank"] -1] += 1
                seat_rank[wind][results[i][wind]["rank"] -1] += 1
                point += float(results[i][wind]["point"])
                count_win += 1 if float(results[i][wind]["point"]) > 0 else 0
                count_lose += 1 if float(results[i][wind]["point"]) < 0 else 0
                count_draw += 1 if float(results[i][wind]["point"]) == 0 else 0
                if eval(str(results[i][wind]["rpoint"])) < 0:
                    count_tobi += 1
                    seat_tobi[g.wind.index(wind)] += 1
                if game_remarks:
                    count_gs += 1

                tmp_msg2 = "{}： {}位 {:>5}00点 ({:>+5.1f}){} {}\n".format(
                    results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"),
                    results[i][wind]["rank"],
                    eval(str(results[i][wind]["rpoint"])),
                    float(results[i][wind]["point"]),
                    gg_flag,
                    ",".join(game_remarks),
                ).replace("-", "▲")

        if command_option["verbose"] and tmp_msg2:
            msg2["戦績"] += tmp_msg1
        else:
            msg2["戦績"] += tmp_msg2

        if myrank: # 対戦結果保存
            for wind in g.wind[0:4]:
                vs_player = results[i][wind]["name"]
                vs_rank = results[i][wind]["rank"]

                if vs_player == target_player[0]: # 自分の成績はスキップ
                    continue
                if not vs_player in versus_matrix.keys():
                    versus_matrix[vs_player] = {"total":0, "win":0, "lose":0}

                versus_matrix[vs_player]["total"] += 1
                if myrank < vs_rank:
                    versus_matrix[vs_player]["win"] += 1
                else:
                    versus_matrix[vs_player]["lose"] += 1

    ### 表示オプション ###
    badge_degree = ""
    if g.config["degree"].getboolean("display", False):
        degree_badge = g.config.get("degree", "badge").split(",")
        degree_counter = [x for x in map(int, g.config.get("degree", "counter").split(","))]
        for i in range(len(degree_counter)):
            if sum(count_rank) >= degree_counter[i]:
                badge_degree = degree_badge[i]

    badge_status = ""
    if g.config["status"].getboolean("display", False):
        status_badge = g.config.get("status", "badge").split(",")
        status_step = g.config.getfloat("status", "step")

        if sum(count_rank) == 0:
            index = 0
        else:
            winper = count_win / sum(count_rank) * 100
            index = 3
            for i in (1, 2, 3):
                if winper <= 50 - status_step * i:
                    index = 4 - i
                if winper >= 50 + status_step * i:
                    index = 2 + i
        badge_status = status_badge[index]

    ### 表示内容 ###
    if len(results) == 0:
        msg1 += f"\tプレイヤー名： {target_player[0]} {badge_degree}\n"
        msg1 += f"\t対戦数：{sum(count_rank)} 戦 ({count_win} 勝 {count_lose} 敗 {count_draw} 分) {badge_status}\n"
        msg2.clear()
    else:
        stime = results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        etime = results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        msg1 += f"\tプレイヤー名： {target_player[0]} {badge_degree}\n"
        msg1 += f"\t集計範囲：{stime} ～ {etime}\n"
        msg1 += f"\t対戦数：{sum(count_rank)} 戦 ({count_win} 勝 {count_lose} 敗 {count_draw} 分) {badge_status}\n"

        if sum(count_rank) > 0:
            msg1 += "\t累積ポイント： {:+.1f}\n".format(point).replace("-", "▲")
            msg1 += "\t平均ポイント： {:+.1f}\n".format(point / sum(count_rank)).replace("-", "▲")
            for i in range(4):
                msg1 += "\t{}位： {:2} 回 ({:.2%})\n".format(i + 1, count_rank[i], count_rank[i] / sum(count_rank))
            msg1 += "\t役満： {:2} 回 ({:.2%})\n".format(count_gs, count_gs / sum(count_rank))
            if not g.config["mahjong"].getboolean("ignore_flying", False):
                msg1 += "\tトビ： {} 回 ({:.2%})\n".format(count_tobi, count_tobi / sum(count_rank))
            msg1 += "\t平均順位： {:1.2f}\n".format(
                sum([count_rank[i] * (i + 1) for i in range(4)]) / sum(count_rank),
            )

            for wind in g.wind[0:4]:
                if sum(seat_rank[wind]) == 0:
                    msg2["座席"] += "\t{}： 0-0-0-0 (-.--)".format(wind)
                else:
                    msg2["座席"] += "\t{}： {}-{}-{}-{} ({:1.2f})".format(
                        wind,
                        seat_rank[wind][0],
                        seat_rank[wind][1],
                        seat_rank[wind][2],
                        seat_rank[wind][3],
                        sum([seat_rank[wind][i] * (i + 1) for i in range(4)]) / sum(seat_rank[wind]),
                        seat_tobi[g.wind.index(wind)],
                    )
                if g.config["mahjong"].getboolean("ignore_flying", False):
                    msg2["座席"] += "\n"
                else:
                    msg2["座席"] += " / トビ： {} 回\n".format(
                         "--" if sum(seat_rank[wind]) == 0 else seat_tobi[g.wind.index(wind)]
                    )

            if not command_option["game_results"]:
                msg2.pop("戦績")

            # 対戦結果
            if command_option["versus_matrix"]:
                # 対戦数順にソート
                tmp_v = {}
                name_list = []

                for i in versus_matrix.keys():
                    tmp_v[i] = versus_matrix[i]["total"]
                for name, total_count in sorted(tmp_v.items(), key=lambda x:x[1], reverse=True):
                    name_list.append(name)

                padding = c.CountPadding(list(versus_matrix.keys()))

                msg2["対戦"] += "\n```\n"
                for i in name_list:
                    msg2["対戦"] += "{}{}：{:3}戦{:3}勝{:3}敗 ({:>7.2%})\n".format(
                    i, " " * (padding - f.translation.len_count(i)),
                    versus_matrix[i]["total"],
                    versus_matrix[i]["win"],
                    versus_matrix[i]["lose"],
                    versus_matrix[i]["win"] / (versus_matrix[i]["total"]),
                )
                msg2["対戦"] += "```"
            else:
                msg2.pop("対戦")
        else:
            msg2.clear()

        msg1 += "\n" + f.remarks(command_option)

    resultdb.close()
    return(msg1.strip(), msg2)
