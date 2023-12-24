import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def slackpost(client, channel, event_ts, argument, command_option):
    """
    成績の集計結果をslackにpostする

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

    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)
    g.logging.info(f"arg: {argument}")
    g.logging.info(f"opt: {command_option}")

    if starttime and endtime:
        # モード切り替え
        versus_mode = False
        if command_option["versus_matrix"]:
            versus_mode = True
            if len(target_player) == 0:
                versus_mode = False
            if len(target_player) == 1 and not command_option["all_player"]:
                versus_mode = False
        if len(target_player) == 1 and not versus_mode: # 個人成績
            msg1, msg2 = details(starttime, endtime, target_player, target_count, command_option)
            res = f.slack_api.post_message(client, channel, msg1)
            for m in msg2.keys():
                f.slack_api.post_message(client, channel, msg2[m] + '\n', res["ts"])
        elif versus_mode: # 直接対戦
            msg1, msg2 = versus(starttime, endtime, target_player, target_count, command_option)
            res = f.slack_api.post_message(client, channel, msg1)
            for m in msg2.keys():
                f.slack_api.post_message(client, channel, msg2[m] + '\n', res["ts"])
        else: # 成績サマリ
            msg1, msg2, msg3 = summary(starttime, endtime, target_player, target_count, command_option)
            res = f.slack_api.post_message(client, channel, msg2)
            if msg1:
                f.slack_api.post_text(client, channel, res["ts"], "", msg1)
            if msg3:
                f.slack_api.post_message(client, channel, msg3, res["ts"])


def summary(starttime, endtime, target_player, target_count, command_option):
    """
    各プレイヤーの累積ポイントを表示

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    target_count : int
        集計するゲーム数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1, msg2, msg3 : text
        slackにpostする内容
    """

    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    tmpdate = f.search.getdata(command_option)
    results = f.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

    r = {}
    game_count = 0
    tobi_count = 0
    first_game = False
    last_game = False

    for i in results.keys():
        if not first_game:
            first_game = results[i]["日付"]
        last_game = results[i]["日付"]
        game_count += 1

        for wind in g.wind[0:4]: # 成績計算
            name = results[i][wind]["name"]

            if not name in r:
                r[name] = {
                    "total": 0,
                    "rank": [0, 0, 0, 0],
                    "tobi": 0,
                }
            r[name]["total"] += round(results[i][wind]["point"], 2)
            r[name]["rank"][results[i][wind]["rank"] -1] += 1

            if eval(str(results[i][wind]["rpoint"])) < 0:
                r[name]["tobi"] += 1

    if not (first_game or last_game):
        return(None, f.message.no_hits(starttime, endtime), None)

    # 獲得ポイント順にソート
    tmp_r = {}
    name_list = []

    for i in r.keys():
        tmp_r[i] = r[i]["total"]

    for name, point in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        if name in ("全員", "all"):
            continue
        if not command_option["guest_skip"] and name == g.guest_name:
            continue
        if not len(target_player) == 0 and not name in target_player:
            continue
        name_list.append(name)
    g.logging.info(f"name_list: {name_list}")

    # 表示
    padding = c.CountPadding(name_list)
    msg1 = ""
    msg2 = "*【成績サマリ】*\n"
    msg3 = ""

    if command_option["score_comparisons"]:
        header = "{} {}： 累積    / 点差 ##\n".format(
            "## 名前", " " * (padding - f.translation.len_count(name) - 2),
        )
        for name in name_list:
            tobi_count += r[name]["tobi"]
            if name_list.index(name) == 0:
                msg1 += "{} {}： {:>+6.1f} / *****\n".format(
                    name, " " * (padding - f.translation.len_count(name)),
                    r[name]["total"],
                ).replace("-", "▲").replace("*", "-")
            else:
                msg1 += "{} {}： {:>+6.1f} / {:>5.1f}\n".format(
                    name, " " * (padding - f.translation.len_count(name)),
                    r[name]["total"],
                    r[name_list[name_list.index(name) - 1]]["total"] - r[name]["total"],
                ).replace("-", "▲")
    else:
        header = "## 名前 : 累積 (平均) / 順位分布 (平均)"
        if g.config["mahjong"].getboolean("ignore_flying", False):
            header += " ##\n"
        else:
            header +=" / トビ ##\n"
        for name in name_list:
            tobi_count += r[name]["tobi"]
            msg1 += "{} {}： {:>+6.1f} ({:>+5.1f})".format(
                name, " " * (padding - f.translation.len_count(name)),
                r[name]["total"],
                r[name]["total"] / sum(r[name]["rank"]),
            ).replace("-", "▲")
            msg1 += " / {}-{}-{}-{} ({:1.2f})".format(
                r[name]["rank"][0], r[name]["rank"][1], r[name]["rank"][2], r[name]["rank"][3],
                sum([r[name]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[name]["rank"]),
            )
            if g.config["mahjong"].getboolean("ignore_flying", False):
                msg1 += "\n"
            else:
                msg1 += f" / {r[name]['tobi']}\n"

    if target_count == 0:
        msg2 += f"\t検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    msg2 += f"\t最初のゲーム：{first_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    msg2 += f"\t最後のゲーム：{last_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    msg2 += f"\t総ゲーム回数： {game_count} 回"
    if g.config["mahjong"].getboolean("ignore_flying", False):
        msg2 += "\n"
    else:
        msg2 += f" / トバされた人（延べ）： {tobi_count} 人\n"

    msg2 += f.remarks(command_option)

    # メモ表示
    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row
    rows = resultdb.execute(
        "select * from remarks where thread_ts between ? and ? order by thread_ts",
        (starttime.timestamp(), endtime.timestamp())
    )
    for row in rows.fetchall():
        name = c.NameReplace(row["name"], command_option)
        if name in name_list:
            msg3 += "\t{}： {} （{}）\n".format(
                datetime.fromtimestamp(float(row["thread_ts"])).strftime('%Y/%m/%d %H:%M'),
                row["matter"],
                name,
            )

    if msg3:
        msg3 = "*【メモ】*\n" + msg3

    return(header + msg1, msg2, msg3)


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

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    tmpdate = f.search.getdata(command_option)
    results = f.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

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


def versus(starttime, endtime, target_player, target_count, command_option):
    """
    直接対戦結果を集計して返す

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー

    target_count: int
        集計するゲーム数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        slackにpostするデータ

    msg2 : dict
        slackにpostするデータ(スレッドに返す)
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]
    g.logging.info(f"date range: {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"target_player: {target_player}")
    g.logging.info(f"command_option: {command_option}")

    tmpdate = f.search.getdata(command_option)
    results = f.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

    msg2 = {}
    msg1 = "*【直接対戦結果】*\n"
    msg1 += f"\tプレイヤー名： {target_player[0]}\n"

    if command_option["all_player"]:
        vs_list = list(set(g.member_list.values()))
        vs_list.remove(target_player[0]) # 自分を除外
        msg1 += f"\t対戦相手：全員\n"
    else:
        vs_list = target_player[1:]
        msg1 += f"\t対戦相手：{', '.join(vs_list)}\n"

    if results.keys():
        msg1 += "\t集計範囲：{} ～ {}\n".format(
            results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M'),
            results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M'),
        )
        msg1 += f.remarks(command_option)
    else:
        msg1 += "\t集計範囲：{} ～ {}\n".format(
            starttime.strftime('%Y/%m/%d %H:%M'),
            endtime.strftime('%Y/%m/%d %H:%M'),
        )
        msg1 += f.remarks(command_option)
        msg2[""] = "対戦記録が見つかりませんでした。\n"

        return(msg1, msg2)

    padding = c.CountPadding(vs_list)
    g.logging.info(f"vs_list: {vs_list} padding: {padding}")

    for versus_player in vs_list:
        # 同卓したゲームの抽出
        vs_game = []
        for i in results.keys():
            vs_flag = [False, False]
            for wind in g.wind[0:4]:
                if target_player[0] == results[i][wind]["name"]:
                    vs_flag[0] = True
                if versus_player == results[i][wind]["name"]:
                    vs_flag[1] = True
            if vs_flag[0] and vs_flag[1]:
                vs_game.append(i)

        ### 対戦結果集計 ###
        win = 0 # 勝ち越し数
        my_aggr = { # 自分の集計結果
            "r_total": 0, # 素点合計
            "total": 0, # ポイント合計
            "rank": [0, 0, 0, 0],
        }
        vs_aggr = { # 相手の集計結果
            "r_total": 0, # 素点合計
            "total": 0, # ポイント合計
            "rank": [0, 0, 0, 0],
        }

        if target_player[0] == versus_player:
            continue

        msg2[versus_player] = "[ {} vs {} ]\n".format(target_player[0], versus_player)

        for i in vs_game:
            for wind in g.wind[0:4]:
                if target_player[0] == results[i][wind]["name"]:
                    r_m = results[i][wind]
                    my_aggr["r_total"] += eval(str(results[i][wind]["rpoint"])) * 100
                    my_aggr["total"] += results[i][wind]["point"]
                    my_aggr["rank"][results[i][wind]["rank"] -1] += 1
                if versus_player == results[i][wind]["name"]:
                    r_v = results[i][wind]
                    vs_aggr["r_total"] += eval(str(results[i][wind]["rpoint"])) * 100
                    vs_aggr["total"] += results[i][wind]["point"]
                    vs_aggr["rank"][results[i][wind]["rank"] -1] += 1

            if r_m["rank"] < r_v["rank"]:
                win += 1

        ### 集計結果出力 ###
        if len(vs_game) == 0:
            msg2.pop(versus_player)
        else:
            msg2[versus_player] += "対戦数： {} 戦 {} 勝 {} 敗\n".format(len(vs_game), win, len(vs_game) - win)
            msg2[versus_player] += "平均素点差： {:+.1f}点\n".format(
                (my_aggr["r_total"] - vs_aggr["r_total"]) / len(vs_game)
            ).replace("-", "▲")
            msg2[versus_player] += "獲得ポイント合計(自分)： {:+.1f}pt\n".format(
                my_aggr["total"]
            ).replace("-", "▲")
            msg2[versus_player] += "獲得ポイント合計(相手)： {:+.1f}pt\n".format(
                vs_aggr["total"]
            ).replace("-", "▲")
            msg2[versus_player] += "順位分布(自分)： {}-{}-{}-{} ({:1.2f})\n".format(
                my_aggr["rank"][0], my_aggr["rank"][1], my_aggr["rank"][2], my_aggr["rank"][3],
                sum([my_aggr["rank"][i] * (i + 1) for i in range(4)]) / sum(my_aggr["rank"]),
            )
            msg2[versus_player] += "順位分布(相手)： {}-{}-{}-{} ({:1.2f})\n".format(
                vs_aggr["rank"][0], vs_aggr["rank"][1], vs_aggr["rank"][2], vs_aggr["rank"][3],
                sum([vs_aggr["rank"][i] * (i + 1) for i in range(4)]) / sum(vs_aggr["rank"]),
            )
            if command_option["game_results"]:
                msg2[versus_player] += "\n[ゲーム結果]\n"
                for i in vs_game:
                    msg2[versus_player] += results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S\n")
                    for wind in g.wind[0:4]:
                        tmp_msg = "\t{}： {}{} / {}位 {:>5}00点 ({}pt)\n".format(
                            wind, results[i][wind]["name"],
                            " " * (padding - f.translation.len_count(results[i][wind]["name"])),
                            results[i][wind]["rank"],
                            eval(str(results[i][wind]["rpoint"])),
                            results[i][wind]["point"],
                        ).replace("-", "▲")

                        if command_option["verbose"]:
                            msg2[versus_player] += tmp_msg
                        elif results[i][wind]["name"] in (target_player[0], versus_player):
                            msg2[versus_player] += tmp_msg

    if not msg2:
        msg2[""] = "直接対戦はありません。\n"

    return(msg1.strip(), msg2)
