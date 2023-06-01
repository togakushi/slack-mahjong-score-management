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


def ranking2(ranking_type, ranking_data, data1, rank = 3): # プレイゲーム数に対する割合/平均/回数
    msg = ""
    namelist = [i for i in ranking_data.keys()]
    data2 = [ranking_data[i]['game_count'] for i in ranking_data.keys()]
    if ranking_type == 2:
        data = data1
    else:
        data = [data1[i]/data2[i] for i in range(len(ranking_data.keys()))]

    for juni in range(1, rank + 1):
        top =  [i for i, j in enumerate(data) if j == max(data)]

        for i in top:
            if ranking_type == 0: # 割合
                msg += "\t{}: {} {}% ({}/{})\n".format(
                    juni,
                    namelist[i],
                    round(data1[i]/data2[i] * 100,2),
                    data1[i],
                    data2[i],
                )
            if ranking_type == 1: # 平均
                msg += "\t{}: {} {} ({}/{})\n".format(
                    juni,
                    namelist[i],
                    round(data1[i]/data2[i], 1),
                    round(data1[i], 1),
                    data2[i],
                )
            if ranking_type == 2: # 回数
                msg += "\t{}: {} {} ({})\n".format(
                    juni,
                    namelist[i],
                    data[i],
                    data2[i],
                )

        popcounter = 0
        for i in top:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
            data1.pop(i - popcounter)
            data2.pop(i - popcounter)
            popcounter += 1

    return(msg)


def ranking3(ranking_type, results, ranking_data, data, rank = 3): # 総ゲーム数に対する割合/回数
    msg = ""
    namelist = [i for i in ranking_data.keys()]

    for juni in range(1, rank + 1):
        top =  [i for i, j in enumerate(data) if j == max(data)]

        for i in top:
            if ranking_type == 0: # 割合
                msg += "\t{}: {} {}% ({}/{})\n".format(
                    juni,
                    namelist[i],
                    round(data[i]/len(results) * 100,2),
                    data[i],
                    len(results),
                )
            if ranking_type == 1: # 回数
                msg += "\t{}: {} {} / {}\n".format(
                    juni,
                    namelist[i],
                    data[i],
                    len(results),
                )

        popcounter = 0
        for i in top:
            namelist.pop(i - popcounter)
            data.pop(i - popcounter)
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
                    'game_count': 0,
                    'total_point': 0,
                    'r1': 0,
                    'r2': 0,
                    'r3': 0,
                    'r4': 0,
                    'tobi': 0,
                }

            ranking_data[name]['game_count'] += 1
            ranking_data[name]['total_point'] += results[i][wind]['point']
            ranking_data[name]['r1'] += 1 if results[i][wind]['rank'] == 1 else 0
            ranking_data[name]['r2'] += 1 if results[i][wind]['rank'] == 2 else 0
            ranking_data[name]['r3'] += 1 if results[i][wind]['rank'] == 3 else 0
            ranking_data[name]['r4'] += 1 if results[i][wind]['rank'] == 4 else 0
            ranking_data[name]['tobi'] += 1 if eval(results[i][wind]['rpoint']) < 0 else 0

    msg = ""
    msg += "\n*ゲーム参加率*\n"
    data = [ranking_data[i]['game_count'] for i in ranking_data.keys()]
    msg += ranking3(0, results, ranking_data, data)

    msg += "\n*総合ポイント*\n"
    data = [round(ranking_data[i]['total_point'],1) for i in ranking_data.keys()]
    msg += ranking2(2, ranking_data, data)

    msg +="\n*平均ポイント*\n"
    data = [ranking_data[i]['total_point'] for i in ranking_data.keys()]
    msg += ranking2(1, ranking_data, data)

    msg += "\n*トップ率*\n"
    data = [ranking_data[i]['r1'] for i in ranking_data.keys()]
    msg += ranking2(0, ranking_data, data)

    msg += "\n*連対率*\n"
    data = [ranking_data[i]['r1']+ranking_data[i]['r2'] for i in ranking_data.keys()]
    msg += ranking2(0, ranking_data, data)

    return(msg)
