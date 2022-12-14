import re
import sqlite3
from datetime import datetime

import command as c
import database as db
import function as f
from function import global_value as g


def pattern(text):
    keyword = g.config["search"].get("keyword", "御無礼")
    pattern1 = re.compile(rf"^{keyword}([^0-9+-]+[0-9+-]+){{4}}")
    pattern2 = re.compile(rf"([^0-9+-]+[0-9+-]+){{4}}{keyword}$")

    text = "".join(text.split())
    if pattern1.search(text) or pattern2.search(text):
        ret = re.sub(rf"^{keyword}|{keyword}$", "", text)
        ret = re.sub(rf"([^0-9+-]+)([0-9+-]+)" * 4, r"\1 \2 \3 \4 \5 \6 \7 \8", ret).split()

    return(ret if "ret" in locals() else False)


def getdata(command_option):
    """
    成績データ取得

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    data : dict
        変換、修正後の成績データ
    """

    # データソースの切り替え
    if command_option["archive"]:
        conn = sqlite3.connect(g.dbfile, detect_types = sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        data = db.common.select_table(cur, command_option)
        conn.close()
    else:
        data = slack_search(command_option)

    # プレイヤー名の正規化、2ゲスト戦除外
    for count in list(data.keys()):
        guest_count = 0
        for wind in ("東家", "南家", "西家", "北家"):
            data[count][wind]["name"] = c.member.NameReplace(data[count][wind]["name"], command_option)

            if g.guest_name in data[count][wind]["name"]:
                guest_count += 1

        if command_option["guest_skip"] and guest_count >= 2:
            pop = data.pop(count)
            g.logging.info(f"[2ゲスト戦除外] {pop}")

    return(data)


def slack_search(command_option):
    """
    過去ログからスコアを検索して返す

    Parameters
    ----------
    command_option : dict
        コマンドオプション

    Returns
    -------
    data : dict
        検索した結果
    """

    keyword = g.config["search"].get("keyword", "御無礼")
    channel = g.config["search"].get("channel", "#麻雀やろうぜ")
    g.logging.info(f"[serach] query:'{keyword} in:{channel}' {command_option}")

    ### データ取得 ###
    response = g.webclient.search_messages(
        query = f"{keyword} in:{channel}",
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query = f"{keyword} in:{channel}",
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
            dt = datetime.fromtimestamp(float(matches[i]["ts"])).replace(microsecond = 0)

            if "elements" in matches[i]["blocks"][0]:
                msg = ""
                tmp = matches[i]["blocks"][0]["elements"][0]["elements"]

                if g.args.verbose:
                    g.logging.info(f"[serach] debug: {dt}, {tmp}")

                for x in range(len(tmp)):
                    if tmp[x]["type"] == "text":
                        msg += tmp[x]["text"]
                msg = pattern(msg)

                if msg:
                    data[count] = {
                        "日付": dt,
                        "東家": {"name": msg[0], "rpoint": msg[1], "rank": None, "point": None},
                        "南家": {"name": msg[2], "rpoint": msg[3], "rank": None, "point": None},
                        "西家": {"name": msg[4], "rpoint": msg[5], "rank": None, "point": None},
                        "北家": {"name": msg[6], "rpoint": msg[7], "rank": None, "point": None},
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
                        data[count][x]["point"] = f.score.CalculationPoint(eval(msg[y]), rank.index(p) + 1)

                    if g.args.verbose:
                        g.logging.info(f"[serach] debug: {data[count]}")

                    count += 1

    return(data)
