import re

from dateutil.relativedelta import relativedelta

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def slackpost(client, channel, argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    title, msg = getdata(starttime, endtime, command_option)
    f.slack_api.post_upload(client, channel, title, msg)


def getdata(starttime, endtime, command_option):
    """
    半荘単位の成績を取得

    Parameters
    ----------
    starttime : date
        出力開始日時

    endtime : date
        出力終了日時

    command_option : dict
        コマンドオプション

    Returns
    -------
    title : str
        slackにpostするタイトル

    msg : text
        slackにpostする内容
    """

    g.logging.info(f"command_option: {command_option}")
    results = c.search.getdata(command_option)

    msg = ""
    title = f"張り付け用集計済みデータ"
    pointsum = g.config["mahjong"].getint("point", 250) * 4

    for i in results.keys():
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            deposit = pointsum - sum([eval(str(results[i][x]["rpoint"])) for x in g.wind])

            msg += "{},<場所>,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                results[i]["日付"].strftime("%Y/%m/%d %H:%M:%S"), deposit,
                results[i]["東家"]["name"], eval(str(results[i]["東家"]["rpoint"])), results[i]["東家"]["rank"], results[i]["東家"]["point"],
                results[i]["南家"]["name"], eval(str(results[i]["南家"]["rpoint"])), results[i]["南家"]["rank"], results[i]["南家"]["point"],
                results[i]["西家"]["name"], eval(str(results[i]["西家"]["rpoint"])), results[i]["西家"]["rank"], results[i]["西家"]["point"],
                results[i]["北家"]["name"], eval(str(results[i]["北家"]["rpoint"])), results[i]["北家"]["rank"], results[i]["北家"]["point"],
                (results[i]["日付"] + relativedelta(hours = -12)).strftime("%Y/%m/%d"),
            )

    return(title, msg)
