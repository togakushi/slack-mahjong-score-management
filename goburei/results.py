import logging
import re
import datetime

from function import global_value as g
from function import common
from function import message
from function import slack_api
from goburei import member
from goburei import search

logging.basicConfig(level = g.logging_level)


# イベントAPI
@g.app.message(re.compile(r"^御無礼成績"))
def handle_goburei_results_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(r"^御無礼成績$", command):
        return

    command_option = {
        "default_action": ["今月"],
        "name_replace": True, # 表記ブレ修正
        "guest_rename": True, # 未登録をゲストに置き換え
        "guest_skip": True, # 2ゲスト戦除外(サマリ用)
        "guest_skip2": False, # 2ゲスト戦除外(個人成績用)
        "results": False, # 戦績表示
        "recursion": True,
    }

    logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


def slackpost(client, channel, argument, command_option):
    target_days, target_player, command_option = common.argument_analysis(argument, command_option)
    starttime, endtime = common.scope_coverage(target_days)

    if starttime and endtime:
        if len(target_player) == 1: # 個人成績
            msg, score = details(starttime, endtime, target_player, command_option)
            if command_option["results"]:
                slack_api.post_message(client, channel, msg + score)
            else: # 戦績は出さない
                    slack_api.post_message(client, channel, msg)
        else: # 成績サマリ
            msg = summary(starttime, endtime, target_player, command_option)
            slack_api.post_text(client, channel, "", msg)


def summary(starttime, endtime, target_player, command_option):
    """
    各プレイヤーの累積ポイントを取得

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    logging.info(f"[results.summary] {command_option} {target_player}")
    results = search.getdata(command_option)

    r = {}
    game_count = 0
    tobi_count = 0
    first_game = False
    last_game = False

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            if not first_game:
                first_game = results[i]["日付"]
            last_game = results[i]["日付"]
            game_count += 1
            for seki in ("東家", "南家", "西家", "北家"): # 成績計算
                name = results[i][seki]["name"]
                if not name in r:
                    r[name] = {
                        "total": 0,
                        "rank": [0, 0, 0, 0],
                        "tobi": 0,
                    }
                r[name]["total"] += round(results[i][seki]["point"], 2)
                r[name]["rank"][results[i][seki]["rank"] -1] += 1
                if eval(results[i][seki]["rpoint"]) < 0:
                    r[name]["tobi"] += 1
                    tobi_count += 1

    tmp_r = {}
    msg = ""
    header = "## 名前 : 累計 (平均) / 順位分布 (平均) / トビ ##\n"

    for i in r.keys():
        tmp_r[i] = r[i]["total"]

    for name, p in sorted(tmp_r.items(), key=lambda x:x[1], reverse=True):
        if not command_option["guest_skip"] and name == "ゲスト１":
            continue
        msg += "{}{}： {:>+6.1f} ({:>+5.1f})".format(
            name, " " * (9 - common.len_count(name)),
            r[name]["total"],
            r[name]["total"] / sum(r[name]["rank"]),
        ).replace("-", "▲")
        msg += " / {}-{}-{}-{} ({:1.2f}) / {}\n".format(
            r[name]["rank"][0], r[name]["rank"][1], r[name]["rank"][2], r[name]["rank"][3],
            sum([r[name]["rank"][i] * (i + 1) for i in range(4)]) / sum(r[name]["rank"]),
            r[name]["tobi"],
        )

    if not (first_game or last_game):
        msg = f"{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')} に御無礼はありません。"
        return(msg)

    footer = "-" * 5 + "\n"
    footer += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"最初のゲーム：{first_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"最後のゲーム：{last_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"ゲーム回数： {game_count} 回 / トバされた人（延べ）： {tobi_count} 人\n"

    remarks = []
    if not command_option["name_replace"]:
        remarks.append("名前ブレ修正なし")
    if not command_option["guest_skip"]:
        remarks.append("2ゲスト戦を含む")
    if remarks:
        footer += f"特記事項：" + "、".join(remarks)

    return(header + msg + footer)


def details(starttime, endtime, target_player, command_option):
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

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg1 : text
        slackにpostする内容(成績データ)

    msg2 : text
        slackにpostする内容(戦績データ)
    """

    # 検索動作を合わせる
    command_option["guest_skip"] = command_option["guest_skip2"]

    logging.info(f"[results.details] {command_option} {target_player}")
    results = search.getdata(command_option)

    if command_option["guest_skip"]:
        msg1 = f"*【個人成績】*\n"
    else:
        msg1 = f"*【個人成績】* (※2ゲスト戦含む)\n"

    msg2 = f"\n*【戦績】*\n"

    point = 0
    count_rank = [0, 0, 0, 0]
    count_tobi = 0
    count_win = 0
    count_lose = 0
    count_draw = 0

    for i in range(len(results)):
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            for seki in ("東家", "南家", "西家", "北家"):
                if target_player[0] == results[i][seki]["name"]:
                    count_rank[results[i][seki]["rank"] -1] += 1
                    point += float(results[i][seki]["point"])
                    count_tobi += 1 if eval(results[i][seki]["rpoint"]) < 0 else 0
                    count_win += 1 if float(results[i][seki]["point"]) > 0 else 0
                    count_lose += 1 if float(results[i][seki]["point"]) < 0 else 0
                    count_draw += 1 if float(results[i][seki]["point"]) == 0 else 0
                    msg2 += "{}： {}位 {:>5}00点 ({:>+5.1f}) {}\n".format(
                        results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"),
                        results[i][seki]["rank"], eval(results[i][seki]["rpoint"]), float(results[i][seki]["point"]),
                        "※" if [results[i][x]["name"] for x in ("東家", "南家", "西家", "北家")].count("ゲスト１") >= 2 else "",
                    ).replace("-", "▲")

    msg1 += f"プレイヤー名： {target_player[0]}\n"
    msg1 += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    msg1 += f"対戦数： {sum(count_rank)} 半荘 ({count_win} 勝 {count_lose} 敗 {count_draw} 分)\n"

    if sum(count_rank) > 0:
        msg1 += "累積ポイント： {:+.1f}\n平均ポイント： {:+.1f}\n".format(
            point, point / sum(count_rank),
        ).replace("-", "▲")
        for i in range(4):
            msg1 += "{}位： {:2} 回 ({:.2%})\n".format(i + 1, count_rank[i], count_rank[i] / sum(count_rank))
        msg1 += "トビ： {} 回 ({:.2%})\n".format(count_tobi, count_tobi / sum(count_rank))
        msg1 += "平均順位： {:1.2f}\n".format(
            sum([count_rank[i] * (i + 1) for i in range(4)]) / sum(count_rank),
        )
    else:
        msg2 += f"記録なし\n"

    return(msg1, msg2)
