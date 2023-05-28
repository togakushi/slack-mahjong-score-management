import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

import command as c
import function as f
from function import global_value as g

commandword = g.config["record"].get("commandword", "御無礼記録")

# イベントAPI
@g.app.message(re.compile(rf"^{commandword}"))
def handle_record_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(rf"^{commandword}$", command):
        return

    command_option = f.configure.command_option_initialization("record")
    g.logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


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

    g.logging.info(f"[record] {command_option}")
    results = c.search.getdata(command_option)

    msg = ""
    title = f"張り付け用集計済みデータ"
    pointsum = g.config["mahjong"].getint("point", 250) * 4

    for i in results.keys():
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
        
            deposit = pointsum - eval(results[i]["東家"]["rpoint"]) - eval(results[i]["南家"]["rpoint"]) - eval(results[i]["西家"]["rpoint"]) - eval(results[i]["北家"]["rpoint"])

            msg += "{},<場所>,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                results[i]["日付"].strftime("%Y/%m/%d %H:%M"), deposit,
                results[i]["東家"]["name"], eval(results[i]["東家"]["rpoint"]), results[i]["東家"]["rank"], results[i]["東家"]["point"],
                results[i]["南家"]["name"], eval(results[i]["南家"]["rpoint"]), results[i]["南家"]["rank"], results[i]["南家"]["point"],
                results[i]["西家"]["name"], eval(results[i]["西家"]["rpoint"]), results[i]["西家"]["rank"], results[i]["西家"]["point"],
                results[i]["北家"]["name"], eval(results[i]["北家"]["rpoint"]), results[i]["北家"]["rank"], results[i]["北家"]["point"],
                (results[i]["日付"] + relativedelta(hours = -12)).strftime("%Y/%m/%d"),
            )

    return(title, msg)
