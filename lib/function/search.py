import re
import sqlite3
from datetime import datetime

import lib.command as c
import lib.function as f
from lib.function import global_value as g


def pattern(text):
    """
    成績記録用フォーマットチェック

    Parameters
    ----------
    text : text
        slackにポストされた内容

    Returns
    -------
    ret : text / False
        フォーマットに一致すればスペース区切りの名前と素点のペア
    """

    keyword = g.config["search"].get("keyword", "終局")
    pattern1 = re.compile(rf"^{keyword}([^0-9+-]+[0-9+-]+){{4}}$")
    pattern2 = re.compile(rf"([^0-9+-]+[0-9+-]+){{4}}{keyword}$")

    # 全角プラス符号(0xff0b)は半角に置換
    text = text.replace(chr(0xff0b), "+")
    # 全角マイナス符号(0x2212)は半角に置換
    text = text.replace(chr(0x2212), "-")

    text = "".join(text.split())
    if pattern1.search(text) or pattern2.search(text):
        ret = re.sub(rf"^{keyword}|{keyword}$", "", text)
        ret = re.sub(rf"([^0-9+-]+)([0-9+-]+)" * 4, r"\1 \2 \3 \4 \5 \6 \7 \8", ret).split()

    return(ret if "ret" in locals() else False)


def for_slack(keyword, channel):
    """
    過去ログからキーワードを検索して返す

    Parameters
    ----------
    keyword : text
        検索キーワード

    channel : text
        チャンネル名

    Returns
    -------
    matches : dict
        検索した結果
    """

    ### 検索クエリ ###
    query = f"{keyword} in:{channel}"
    after = g.config["search"].get("after")
    if after:
        try:
            datetime.fromisoformat(after) # フォーマットチェック
            query = f"{keyword} in:{channel} after:{after}"
        except:
            g.logging.error(f"Incorrect date string: {after}")

    g.logging.info(f"{query=}")

    ### データ取得 ###
    response = g.webclient.search_messages(
        query = query,
        sort = "timestamp",
        sort_dir = "asc",
        count = 100
    )
    matches = response["messages"]["matches"] # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query = query,
            sort = "timestamp",
            sort_dir = "asc",
            count = 100,
            page = p
        )
        matches += response["messages"]["matches"] # 2ページ目以降

    return(matches)


def for_database(cur, first_ts = False):
    """
    データベースからスコアを検索して返す

    Parameters
    ----------
    cur: obj
        データベースのカーソル

    first_ts: float
        検索を開始する時刻

    Returns
    -------
    data : dict
        検索した結果
    """

    if not first_ts:
        return(None)

    data ={}
    rows = cur.execute(f"select * from result where ts >= ?", (first_ts,))
    for row in rows.fetchall():
        ts = row["ts"]
        data[ts] = []
        data[ts].append(row["p1_name"])
        data[ts].append(row["p1_str"])
        data[ts].append(row["p2_name"])
        data[ts].append(row["p2_str"])
        data[ts].append(row["p3_name"])
        data[ts].append(row["p3_str"])
        data[ts].append(row["p4_name"])
        data[ts].append(row["p4_str"])

    return(data)


def game_result(data, command_option):
    """
    slackの検索ログからゲームの結果を返す

    Parameters
    ----------
    data : dict
        slackの検索ログ

    command_option : dict
        検索オプション

    Returns
    -------
    matches : dict
        検索した結果
    """

    result = {}
    for i in range(len(data)):
        if "blocks" in data[i]:
            if data[i]["user"] in g.ignore_userid: # 除外ユーザからのポストは集計対象から外す
                g.logging.info(f"skip: {data[i]}")
                continue

            ts = data[i]["ts"]
            if "elements" in data[i]["blocks"][0]:
                tmp_msg = ""
                elements = data[i]["blocks"][0]["elements"][0]["elements"]

                for x in range(len(elements)):
                    if elements[x]["type"] == "text":
                        tmp_msg += elements[x]["text"]

                # 結果報告フォーマットに一致したポストの処理
                msg = f.search.pattern(tmp_msg)
                if msg:
                    p1_name = c.member.NameReplace(msg[0], command_option)
                    p2_name = c.member.NameReplace(msg[2], command_option)
                    p3_name = c.member.NameReplace(msg[4], command_option)
                    p4_name = c.member.NameReplace(msg[6], command_option)
                    result[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7]]
                    g.logging.trace(f"{ts}: {result[ts]}") # type: ignore

    if len(result) == 0:
        return(None)
    else:
        return(result)
