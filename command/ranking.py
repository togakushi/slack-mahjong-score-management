import re

import command as c
import function as f
from function import global_value as g

commandword = g.config["ranking"].get("commandword", "御無礼ランキング")
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

    msg = getdata(starttime, endtime, target_player, target_count, command_option)
    f.slack_api.post_message(client, channel, msg)


def ranking(ranking_type, results, ranking_data, keyword, rank = 3):
    msg = ""
    namelist = [i for i in ranking_data.keys()]
    raw_data = [ranking_data[i][keyword] for i in ranking_data.keys()]
    game_count = [ranking_data[i]["game_count"] for i in ranking_data.keys()]

    if ranking_type == 0 or ranking_type == 1:
        data = [raw_data[i] / game_count[i] for i in range(len(ranking_data.keys()))]
    elif ranking_type == 4:
        data = [raw_data[i] / len(results) for i in range(len(ranking_data.keys()))]
    else:
        data = [ranking_data[i][keyword] for i in ranking_data.keys()]

    # 規定打数チェック
    popcounter = 0
    for i in range(len(namelist)):
        if len(results) * 0.05 > game_count[i - popcounter]:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            raw_data.pop(i - popcounter)
            game_count.pop(i - popcounter)
            popcounter += 1

    for juni in range(1, rank + 1):
        top =  [i for i, j in enumerate(data) if j == max(data)]

        for i in top:
            if ranking_type == 0: # プレイゲーム数に対する割合
                msg += "\t{}: {}\t{:.2%}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    data[i],
                    round(raw_data[i], 1),
                    game_count[i],
                )
            if ranking_type == 1: # プレイゲーム数に対する平均
                msg += "\t{}: {}\t{}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    round(data[i], 1),
                    round(raw_data[i], 1),
                    game_count[i],
                )
            if ranking_type == 2: # プレイゲーム数に対する回数
                msg += "\t{}: {}\t{}\t({}ゲーム)\n".format(
                    juni, namelist[i],
                    round(raw_data[i], 1),
                    game_count[i],
                )
            if ranking_type == 4: # 総ゲーム数に対する割合
                msg += "\t{}: {}\t{:.2%}\t({}/{}ゲーム)\n".format(
                    juni, namelist[i],
                    data[i],
                    round(raw_data[i], 1),
                    len(results),
                )

        popcounter = 0
        for i in top:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            raw_data.pop(i - popcounter)
            game_count.pop(i - popcounter)
            popcounter += 1

    return(msg)

def ranking2(ranking_type, results, ranking_data, keyword, rank = 3):
    msg = ""
    namelist = [i for i in ranking_data.keys()]
    raw_data = [ranking_data[i][keyword] for i in ranking_data.keys()]
    game_count = [ranking_data[i]["game_count"] for i in ranking_data.keys()]

    data = [raw_data[i] / game_count[i] for i in range(len(ranking_data.keys()))]

    # 規定打数チェック
    popcounter = 0
    for i in range(len(namelist)):
        if len(results) * 0.05 > game_count[i - popcounter]:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            raw_data.pop(i - popcounter)
            game_count.pop(i - popcounter)
            popcounter += 1

    for juni in range(1, rank + 1):
        top =  [i for i, j in enumerate(data) if j == min(data)]

        for i in top:
            if ranking_type == 0:
                msg += "\t{}: {}\t{:1.2f}\n".format(
                    juni, namelist[i],
                    data[i],
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

    g.logging.info(f"[ranking] {starttime} {endtime} {target_player} {target_count} {command_option}")
    tmpdate = c.search.getdata(command_option)
    results = c.search.game_select(starttime, endtime, target_player, target_count,tmpdate)

    ranking_data = {}
    for i in results.keys():
        for wind in ("東家", "南家", "西家", "北家"):
            name = results[i][wind]["name"]
            if not name in ranking_data:
                ranking_data[name] = {
                    "game_count": 0,
                    "total_point": 0,
                    "r1": 0,
                    "r2": 0,
                    "r3": 0,
                    "r4": 0,
                    "ranksum": 0,
                    "success": 0,
                    'tobi': 0,
                }

            ranking_data[name]['game_count'] += 1
            ranking_data[name]['total_point'] += results[i][wind]['point']
            ranking_data[name]['r1'] += 1 if results[i][wind]['rank'] == 1 else 0
            ranking_data[name]['r2'] += 1 if results[i][wind]['rank'] == 2 else 0
            ranking_data[name]['r3'] += 1 if results[i][wind]['rank'] == 3 else 0
            ranking_data[name]['r4'] += 1 if results[i][wind]['rank'] == 4 else 0
            ranking_data[name]["ranksum"] += results[i][wind]['rank']
            ranking_data[name]["success"] += 1 if results[i][wind]['rank'] <= 2 else 0 # 連対率
            #ranking_data[name]['tobi'] += 1 if eval(results[i][wind]['rpoint']) < 0 else 0

    stime = results[min(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
    etime = results[max(results.keys())]["日付"].strftime('%Y/%m/%d %H:%M')
    msg = "\n*【ランキング(テスト中)】*\n"
    msg += f"\t集計範囲：{stime} ～ {etime}\n"
    msg += f"\t集計ゲーム数：{len(results)}\t(規定数：{int(len(results) * 0.05 + 1)})\n"

    msg += "\n*ゲーム参加率*\n"
    msg += ranking(4, results, ranking_data, "game_count")

    msg += "\n*総合ポイント*\n"
    msg += ranking(2, results, ranking_data, "total_point")

    msg +="\n*平均ポイント*\n"
    msg += ranking(1, results, ranking_data, "total_point")

    msg += "\n*トップ率*\n"
    msg += ranking(0, results, ranking_data, "r1")

    msg += "\n*連対率*\n"
    msg += ranking(0, results, ranking_data, "success")

    msg += "\n*平均順位*\n"
    msg += ranking2(0, results, ranking_data, "ranksum")

    return(msg)
