import re

from function import global_value as g
from function import common
from function import slack_api
from goburei import search


# イベントAPI
@g.app.message(re.compile(r"^御無礼(記録|結果)$"))
def handle_goburei_record_evnts(client, context):
    title, msg = getdata(name_replace = True, guest_skip = True)
    slack_api.post_upload(client, context.channel_id, title, msg)


def getdata(name_replace = True, guest_skip = True): # 御無礼結果
    """
    半荘単位の成績を取得

    Parameters
    ----------
    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default True
        2ゲスト戦の除外

    Returns
    -------
    title : str
        slackにポストするタイトル

    msg : text
        slackにポストする内容
    """

    results = search.getdata(name_replace = name_replace, guest_skip = guest_skip)

    if name_replace:
        title = f"張り付け用集計済みデータ"
    else:
        title = f"集計済みデータ(名前ブレ修正なし)"

    msg = ""
    for i in range(len(results)):
        deposit = 1000 - eval(results[i]["東家"]["rpoint"]) - eval(results[i]["南家"]["rpoint"]) - eval(results[i]["西家"]["rpoint"]) - eval(results[i]["北家"]["rpoint"])
        msg += "{},<場所>,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
            results[i]["日付"].strftime("%Y/%m/%d %H:%M"), deposit,
            results[i]["東家"]["name"], eval(results[i]["東家"]["rpoint"]), results[i]["東家"]["rank"], results[i]["東家"]["point"],
            results[i]["南家"]["name"], eval(results[i]["南家"]["rpoint"]), results[i]["南家"]["rank"], results[i]["南家"]["point"],
            results[i]["西家"]["name"], eval(results[i]["西家"]["rpoint"]), results[i]["西家"]["rank"], results[i]["西家"]["point"],
            results[i]["北家"]["name"], eval(results[i]["北家"]["rpoint"]), results[i]["北家"]["rank"], results[i]["北家"]["point"],
        )

    return(title, msg)
