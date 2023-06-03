import re

import command as c
import function as f
from function import global_value as g

commandword = g.config["results"].get("commandword", "御無礼成績")
g.logging.info(f"[import] results {commandword}")


# イベントAPI
@g.app.message(re.compile(rf"^{commandword}"))
def handle_results_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(rf"^{commandword}$", command):
        return

    command_option = f.configure.command_option_initialization("results")
    g.logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


def slackpost(client, channel, argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    if starttime and endtime:
        if len(target_player) == 1: # 個人成績
            msg1, msg2, msg3 = details(starttime, endtime, target_player, target_count, command_option)
            res = f.slack_api.post_message(client, channel, msg1)
            if msg2:
                f.slack_api.post_message(client, channel, msg2, res["ts"])
            if msg3:
                f.slack_api.post_message(client, channel, msg3, res["ts"])
        else: # 成績サマリ
            msg = summary(starttime, endtime, target_player, target_count, command_option)
            f.slack_api.post_text(client, channel, "", msg)


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

    target_count: int
        集計するゲーム数

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    g.logging.info(f"[results.summary] {starttime} {endtime} {target_player} {target_count} {command_option}")
    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

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

        for wind in ("東家", "南家", "西家", "北家"): # 成績計算
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
        return(f.message.no_hits(starttime, endtime))

    # 獲得ポイント順にソート
    tmp_r = {}
    name_list = []

    for i in r.keys():
        tmp_r[i] = r[i]["total"]

    for name, point in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        if not command_option["guest_skip"] and name == g.guest_name:
            continue
        if not len(target_player) == 0 and not name in target_player:
            continue
        name_list.append(name)
    g.logging.info(f"[results.summary] {name_list}")

    # 表示
    padding = max([f.translation.len_count(x) for x in name_list])
    msg = ""

    if command_option["score_comparisons"]:
        header = "{} {}： 累積    / 点差 ##\n".format(
            "## 名前", " " * (padding - f.translation.len_count(name) - 2),
        )
        for name in name_list:
            tobi_count += r[name]["tobi"]
            if name_list.index(name) == 0:
                msg += "{} {}： {:>+6.1f} / *****\n".format(
                    name, " " * (padding - f.translation.len_count(name)),
                    r[name]["total"],
                ).replace("-", "▲").replace("*", "-")
            else:
                msg += "{} {}： {:>+6.1f} / {:>5.1f}\n".format(
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
            msg += "{} {}： {:>+6.1f} ({:>+5.1f})".format(
                name, " " * (padding - f.translation.len_count(name)),
                r[name]["total"],
                r[name]["total"] / sum(r[name]["rank"]),
            ).replace("-", "▲")
            msg += " / {}-{}-{}-{} ({:1.2f})".format(
                r[name]["rank"][0], r[name]["rank"][1], r[name]["rank"][2], r[name]["rank"][3],
                sum([r[name]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[name]["rank"]),
            )
            if g.config["mahjong"].getboolean("ignore_flying", False):
                msg += "\n"
            else:
                msg += f" / {r[name]['tobi']}\n"

    footer = "-" * 5 + "\n"
    if target_count == 0:
        footer += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"最初のゲーム：{first_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"最後のゲーム：{last_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"総ゲーム回数： {game_count} 回"
    if g.config["mahjong"].getboolean("ignore_flying", False):
        footer += "\n"
    else:
        footer += f" / トバされた人（延べ）： {tobi_count} 人\n"

    footer += f.remarks(command_option, starttime)

    return(header + msg + footer)


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
        slackにpostする内容戦績データ)
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]

    g.logging.info(f"[results.summary] {starttime} {endtime} {target_player} {target_count} {command_option}")
    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

    msg1 = f"*【個人成績】*\n"
    msg2 = f"\n*【戦績】*\n"
    msg3 = f"\n*【対戦結果】*\n"

    point = 0
    count_rank = [0, 0, 0, 0]
    count_tobi = 0
    count_win = 0
    count_lose = 0
    count_draw = 0
    versus_matrix = {}

    ### 集計 ###
    for i in results.keys():
        myrank = None

        for wind in ("東家", "南家", "西家", "北家"):
            if target_player[0] == results[i][wind]["name"]:
                myrank = results[i][wind]["rank"]
                count_rank[results[i][wind]["rank"] -1] += 1
                point += float(results[i][wind]["point"])
                count_tobi += 1 if eval(str(results[i][wind]["rpoint"])) < 0 else 0
                count_win += 1 if float(results[i][wind]["point"]) > 0 else 0
                count_lose += 1 if float(results[i][wind]["point"]) < 0 else 0
                count_draw += 1 if float(results[i][wind]["point"]) == 0 else 0
                msg2 += "{}： {}位 {:>5}00点 ({:>+5.1f}) {}\n".format(
                    results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"),
                    results[i][wind]["rank"], eval(str(results[i][wind]["rpoint"])), float(results[i][wind]["point"]),
                    "※" if [results[i][x]["name"] for x in ("東家", "南家", "西家", "北家")].count(g.guest_name) >= 2 else "",
                ).replace("-", "▲")

        if myrank: # 対戦結果保存
            for wind in ("東家", "南家", "西家", "北家"):
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
        msg1 += f"プレイヤー名： {target_player[0]} {badge_degree}\n"
        msg1 += f"対戦数：{sum(count_rank)} 戦 ({count_win} 勝 {count_lose} 敗 {count_draw} 分) {badge_status}\n"
        msg2 = ""
        msg3 = ""
    else:
        stime = results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        etime = results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        msg1 += f"プレイヤー名： {target_player[0]} {badge_degree}\n"
        msg1 += f"集計範囲：{stime} ～ {etime}\n"
        msg1 += f"対戦数：{sum(count_rank)} 戦 ({count_win} 勝 {count_lose} 敗 {count_draw} 分) {badge_status}\n"

        if sum(count_rank) > 0:
            msg1 += "累積ポイント： {:+.1f}\n平均ポイント： {:+.1f}\n".format(
                point, point / sum(count_rank),
            ).replace("-", "▲")
            for i in range(4):
                msg1 += "{}位： {:2} 回 ({:.2%})\n".format(i + 1, count_rank[i], count_rank[i] / sum(count_rank))
            if not g.config["mahjong"].getboolean("ignore_flying", False):
                msg1 += "トビ： {} 回 ({:.2%})\n".format(count_tobi, count_tobi / sum(count_rank))
            msg1 += "平均順位： {:1.2f}\n".format(
                sum([count_rank[i] * (i + 1) for i in range(4)]) / sum(count_rank),
            )

        if command_option["game_results"]:
            if not command_option["guest_skip"]:
                msg2 += "※：2ゲスト戦\n"
        else:
            msg2 = ""

        if command_option["versus_matrix"]:
            # 対戦数順にソート
            tmp_v = {}
            name_list = []

            for i in versus_matrix.keys():
                tmp_v[i] = versus_matrix[i]["total"]
            for name, total_count in sorted(tmp_v.items(), key=lambda x:x[1], reverse=True):
                name_list.append(name)

            padding = max([f.translation.len_count(x) for x in versus_matrix.keys()])
            msg3 += "\n```\n"
            for i in name_list:
                msg3 += "{}{}：{:3}戦{:3}勝{:3}敗 ({:>7.2%})\n".format(
                i, " " * (padding - f.translation.len_count(i)),
                versus_matrix[i]["total"],
                versus_matrix[i]["win"],
                versus_matrix[i]["lose"],
                versus_matrix[i]["win"] / (versus_matrix[i]["total"]),
            )
            msg3 += "```"
        else:
            msg3 = ""

        msg1 += "\n" + f.remarks(command_option, starttime)

    return(msg1, msg2, msg3)
