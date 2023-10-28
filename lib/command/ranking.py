import re

import lib.command as c
import lib.function as f
from lib.function import global_value as g

commandword = g.config["ranking"].get("commandword", "麻雀ランキング")
g.logging.info(f"[import] ranking {commandword}")


# イベントAPI
@g.app.message(re.compile(rf"^{commandword}"))
def handle_ranking_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(rf"^{commandword}$", command):
        return

    command_option = f.configure.command_option_initialization("ranking")
    g.logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


def slackpost(client, channel, argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    msg1, msg2 = getdata(starttime, endtime, target_player, target_count, command_option)
    res = f.slack_api.post_message(client, channel, msg1)
    if msg2:
        f.slack_api.post_message(client, channel, msg2, res["ts"])


def put_ranking(ranking_type, reversed, results, ranking_data, keyword, command_option):
    msg = ""
    namelist = [i for i in ranking_data.keys()]
    raw_data = [ranking_data[i][keyword] for i in ranking_data.keys()]
    game_count = [ranking_data[i]["game_count"] for i in ranking_data.keys()]
    padding = c.CountPadding(results)

    if ranking_type in [0, 1, 5]:
        data = [raw_data[i] / game_count[i] for i in range(len(ranking_data.keys()))]
    elif ranking_type == 4:
        data = [raw_data[i] / len(results) for i in range(len(ranking_data.keys()))]
    else:
        data = [ranking_data[i][keyword] for i in ranking_data.keys()]

    # 規定打数チェック
    popcounter = 0
    for i in range(len(namelist)):
        if int(len(results) * command_option["stipulated_rate"] + 1) >= game_count[i - popcounter]:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            raw_data.pop(i - popcounter)
            game_count.pop(i - popcounter)
            popcounter += 1

    for juni in range(1, command_option["ranked"] + 1):
        if reversed:
            top =  [i for i, j in enumerate(data) if j == min(data)]
        else:
            top =  [i for i, j in enumerate(data) if j == max(data)]

        for i in top:
            if ranking_type == 0: # プレイゲーム数に対する割合
                msg += "\t{}: {}{} {:.2%}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    " " * (padding - f.translation.len_count(namelist[i])),
                    data[i],
                    round(raw_data[i], 1),
                    game_count[i],
                )
            if ranking_type == 1: # プレイゲーム数に対する平均
                msg += "\t{}: {}{} {}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    " " * (padding - f.translation.len_count(namelist[i])),
                    round(data[i], 1),
                    round(raw_data[i], 1),
                    game_count[i],
                ).replace("-", "▲")
            if ranking_type == 2: # プレイゲーム数に対する回数
                msg += "\t{}: {}{} {}\t({}ゲーム)\n".format(
                    juni, namelist[i],
                    " " * (padding - f.translation.len_count(namelist[i])),
                    round(raw_data[i], 1),
                    game_count[i],
                ).replace("-", "▲")
            if ranking_type == 4: # 総ゲーム数に対する割合
                msg += "\t{}: {}{} {:.2%}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    " " * (padding - f.translation.len_count(namelist[i])),
                    data[i],
                    round(raw_data[i], 1),
                    len(results),
                )
            if ranking_type == 5: # 平均順位専用専用
                msg += "\t{}: {}{} {:1.3f}\t({}ゲーム)\n".format(
                    juni, namelist[i],
                    " " * (padding - f.translation.len_count(namelist[i])),
                    data[i],
                    game_count[i],
                )

        popcounter = 0
        for i in top:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            raw_data.pop(i - popcounter)
            game_count.pop(i - popcounter)
            popcounter += 1

    return(msg)


def getdata(starttime, endtime, target_player, target_count, command_option):
    """
    xxxを取得

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

    g.logging.info(f"[ranking] {starttime} {endtime}  target_count: {target_count}")
    g.logging.info(f"[ranking] target_player: {target_player}")
    g.logging.info(f"[ranking] command_option: {command_option}")

    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count, tmpdate)

    ranking_data = {}
    origin_point = g.config["mahjong"].getint("point", 250) # 配給原点
    return_point = g.config["mahjong"].getint("return", 300) # 返し点
    for i in results.keys():
        g.logging.trace(results[i])
        for wind in g.wind[0:4]:
            name = results[i][wind]["name"]
            if not name in ranking_data:
                ranking_data[name] = {
                    "game_count": 0,
                    "total_point": 0,
                    "r1": 0, "r2": 0, "r3": 0, "r4": 0, # 獲得順位
                    "ranksum": 0, # 平均順位
                    "success": 0, # 連対率
                    "not_las": 0, # ラス回避
                    "tobi": 0,
                    "in_exp1": 0, "in_exp2": 0, # 半荘収支
                }

            ranking_data[name]["game_count"] += 1
            ranking_data[name]["total_point"] += results[i][wind]["point"]
            ranking_data[name]["r1"] += 1 if results[i][wind]["rank"] == 1 else 0
            ranking_data[name]["r2"] += 1 if results[i][wind]["rank"] == 2 else 0
            ranking_data[name]["r3"] += 1 if results[i][wind]["rank"] == 3 else 0
            ranking_data[name]["r4"] += 1 if results[i][wind]["rank"] == 4 else 0
            ranking_data[name]["ranksum"] += results[i][wind]["rank"] # 平均順位
            ranking_data[name]["success"] += 1 if results[i][wind]["rank"] <= 2 else 0 # 連対率
            ranking_data[name]["not_las"] += 1 if results[i][wind]["rank"] != 4 else 0 # ラス回避
            ranking_data[name]["tobi"] += 1 if eval(str(results[i][wind]["rpoint"])) < 0 else 0
            ranking_data[name]["in_exp1"] += eval(str(results[i][wind]["rpoint"])) - origin_point # 収支1
            ranking_data[name]["in_exp2"] += eval(str(results[i][wind]["rpoint"])) - return_point # 収支2

    if len(results) == 0:
        msg1 = f.message.no_hits(starttime, endtime)
        msg2 = None
    else:
        stime = results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        etime = results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
        msg1 = "\n*【ランキング】*\n"
        msg1 += f"\t集計範囲：{stime} ～ {etime}\n"
        msg1 += f"\t集計ゲーム数：{len(results)}\t(規定数：{int(len(results) * command_option['stipulated_rate'] + 2)} 以上)\n"
        msg1 += f.remarks(command_option, starttime)

        msg2 = ""
        msg2 += "\n*ゲーム参加率*\n" + put_ranking(4, False, results, ranking_data, "game_count", command_option)
        msg2 += "\n*累積ポイント*\n" + put_ranking(2, False, results, ranking_data, "total_point", command_option)
        msg2 += "\n*平均ポイント*\n" + put_ranking(1, False, results, ranking_data, "total_point", command_option)
        msg2 += "\n*平均収支1* (最終素点-配給原点)/ゲーム数\n" + put_ranking(1, False, results, ranking_data, "in_exp1", command_option)
        msg2 += "\n*平均収支2* (最終素点-返し点)/ゲーム数\n" + put_ranking(1, False, results, ranking_data, "in_exp2", command_option)
        msg2 += "\n*トップ率*\n" + put_ranking(0, False, results, ranking_data, "r1", command_option)
        msg2 += "\n*連対率*\n" + put_ranking(0, False, results, ranking_data, "success", command_option)
        msg2 += "\n*ラス回避率*\n" + put_ranking(0, False, results, ranking_data, "not_las", command_option)
        msg2 += "\n*トビ率*\n" + put_ranking(0, True, results, ranking_data, "tobi", command_option)
        msg2 += "\n*平均順位*\n" + put_ranking(5, True, results, ranking_data, "ranksum", command_option)

    return(msg1, msg2)
