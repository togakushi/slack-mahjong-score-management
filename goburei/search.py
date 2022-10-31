import re
import datetime

from function import global_value as g
from function import common
from function import score
from goburei import member


def pattern(text):
    pattern1 = re.compile(r"^御無礼 ?([^0-9+-]+ ?[0-9+-]+ ?){4}")
    pattern2 = re.compile(r"( ?[^0-9+-]+ ?[0-9+-]+){4} ?御無礼$")
    text = "".join(text.split())

    if pattern1.search(text) or pattern2.search(text):
        ret = text.replace("御無礼", "")
        ret = re.sub(r"([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)([^0-9+-]+)([0-9+-]+)", r"\1 \2 \3 \4 \5 \6 \7 \8", ret)
        ret = ret.split()

    return(ret if "ret" in locals() else False)


def getdata(name_replace = True, guest_skip = True):
    """
    過去ログからスコアを検索して返す

    Parameters
    ----------
    name_replace : bool, default True
        プレイヤー名の表記ゆれを修正

    guest_skip : bool, default True
        2ゲスト戦の除外

    Returns
    -------
    data : dict
        検索した結果
    """

    ### データ取得 ###
    response = g.webclient.search_messages(
        query = "御無礼 in:#麻雀やろうぜ",
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query = "御無礼 in:#麻雀やろうぜ",
            sort = "timestamp",
            sort_dir = "asc",
            count = 100,
            page = p
        )
        matches += response["messages"]["matches"] # 2ページ目以降

    ### データ加工 ###
    seat = {
        "東家": 0.000004, "南家": 0.000003, "西家": 0.000002, "北家": 0.000001,
    }

    data = {}
    count = 0
    for i in range(len(matches)):
        if "blocks" in matches[i]:
            dt = datetime.datetime.fromtimestamp(float(matches[i]["ts"]))

            if "elements" in matches[i]["blocks"][0]:
                msg = ""
                tmp = matches[i]["blocks"][0]["elements"][0]["elements"]
                for x in range(len(tmp)):
                    if tmp[x]["type"] == "text":
                        msg += tmp[x]["text"]
                msg = pattern(msg)

                if msg:
                    if name_replace: # 表記ブレの修正
                        for x in (0, 2, 4, 6):
                            msg[x] = member.NameReplace(msg[x])

                    if guest_skip: # 2ゲスト戦の除外
                        if msg.count("ゲスト１") >= 2:
                            continue

                    data[count] = {
                        "日付": dt,
                        "東家": {"name": msg[0], "rpoint": msg[1], "rank": None, "point": 0},
                        "南家": {"name": msg[2], "rpoint": msg[3], "rank": None, "point": 0},
                        "西家": {"name": msg[4], "rpoint": msg[5], "rank": None, "point": 0},
                        "北家": {"name": msg[6], "rpoint": msg[7], "rank": None, "point": 0},
                    }

                    ### 順位取得 ###
                    rank = [
                        eval(msg[1]) + seat["東家"],
                        eval(msg[3]) + seat["南家"],
                        eval(msg[5]) + seat["西家"],
                        eval(msg[7]) + seat["北家"],
                    ]
                    rank.sort()
                    rank.reverse()

                    for x, y in [("東家", 1), ("南家", 3), ("西家", 5), ("北家", 7)]:
                        p = eval(msg[y]) + seat[x]
                        data[count][x]["rank"] = rank.index(p) + 1
                        data[count][x]["point"] = score.CalculationPoint(eval(msg[y]), rank.index(p) + 1)

                    count += 1

    return(data)
