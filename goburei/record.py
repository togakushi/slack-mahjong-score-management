import re
import datetime

from function import global_value as g
from function import common
from function import slack_api
from goburei import search


# イベントAPI
@g.app.message(re.compile(r"^御無礼(記録|結果)"))
def handle_goburei_record_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(r"^御無礼(記録|結果)$", command):
        return

    command_option = {
        "default_action": ["全部"],
        "name_replace": True, # 名前揺らぎ修正
        "guest_rename": True, # 未登録をゲストに置き換え
        "guest_skip": True, # 2ゲスト戦除外
        "results": False,
        "recursion": True,
    }

    g.logging.info(f"[{command}] {command_option} {argument}")
    target_days, target_player, command_option = common.argument_analysis(argument, command_option)

    title, msg = getdata(command_option)
    slack_api.post_upload(client, context.channel_id, title, msg)


def getdata(command_option): # 御無礼結果
    """
    半荘単位の成績を取得

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    title : str
        slackにpostするタイトル

    msg : text
        slackにpostする内容
    """

    results = search.getdata(command_option)

    if command_option["name_replace"]:
        title = f"張り付け用集計済みデータ"
    else:
        title = f"集計済みデータ(名前ブレ修正なし)"

    msg = ""
    for i in range(len(results)):
        if results[i]["日付"].hour < 12:
            aggregate_date = results[i]["日付"] - datetime.timedelta(days = 1)
        else:
            aggregate_date = results[i]["日付"]

        deposit = 1000 - eval(results[i]["東家"]["rpoint"]) - eval(results[i]["南家"]["rpoint"]) - eval(results[i]["西家"]["rpoint"]) - eval(results[i]["北家"]["rpoint"])

        msg += "{},<場所>,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
            results[i]["日付"].strftime("%Y/%m/%d %H:%M"), deposit,
            results[i]["東家"]["name"], eval(results[i]["東家"]["rpoint"]), results[i]["東家"]["rank"], results[i]["東家"]["point"],
            results[i]["南家"]["name"], eval(results[i]["南家"]["rpoint"]), results[i]["南家"]["rank"], results[i]["南家"]["point"],
            results[i]["西家"]["name"], eval(results[i]["西家"]["rpoint"]), results[i]["西家"]["rank"], results[i]["西家"]["point"],
            results[i]["北家"]["name"], eval(results[i]["北家"]["rpoint"]), results[i]["北家"]["rank"], results[i]["北家"]["point"],
            aggregate_date.strftime("%Y/%m/%d"),
        )

    return(title, msg)
