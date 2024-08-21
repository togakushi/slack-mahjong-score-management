import re
from datetime import datetime

import regex_spm

import lib.command as c
import lib.function as f
from lib.function import global_value as g


class Regexes:
    keyword = g.config["search"].get("keyword", "終局")
    pattern1 = re.compile(
        rf"^({keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern2 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})$"
    )
    pattern3 = re.compile(
        rf"^({keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern4 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})\((.+?)\)$"
    )


def pattern(text):
    """
    成績記録用フォーマットチェック

    Parameters
    ----------
    text : text
        slackにポストされた内容

    Returns
    -------
    msg : text / False
        フォーマットに一致すればスペース区切りの名前と素点のペア
    """

    # 記号を置換
    replace_chr = [
        (chr(0xff0b), "+"),  # 全角プラス符号
        (chr(0x2212), "-"),  # 全角マイナス符号
        (chr(0xff08), "("),  # 全角丸括弧
        (chr(0xff09), ")"),  # 全角丸括弧
        (chr(0x2017), "_"),  # DOUBLE LOW LINE(半角)
    ]
    for z, h in replace_chr:
        text = text.replace(z, h)

    # パターンマッチング
    match regex_spm.fullmatch_in("".join(text.split())):
        case Regexes.pattern1 as m:
            msg = [m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], None]
        case Regexes.pattern2 as m:
            msg = [m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], None]
        case Regexes.pattern3 as m:
            msg = [m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[2]]
        case Regexes.pattern4 as m:
            msg = [m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[10]]
        case _:
            msg = False

    return (msg)


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

    # 検索クエリ
    query = f"{keyword} in:{channel}"
    after = g.config["search"].get("after")
    if after:
        try:
            datetime.fromisoformat(after)  # フォーマットチェック
            query = f"{keyword} in:{channel} after:{after}"
        except Exception:
            g.logging.error(f"Incorrect date string: {after}")

    g.logging.info(f"{query=}")

    # --- データ取得
    response = g.webclient.search_messages(
        query=query,
        sort="timestamp",
        sort_dir="asc",
        count=100
    )
    matches = response["messages"]["matches"]  # 1ページ目

    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.webclient.search_messages(
            query=query,
            sort="timestamp",
            sort_dir="asc",
            count=100,
            page=p
        )
        matches += response["messages"]["matches"]  # 2ページ目以降

    return (matches)


def for_database(cur, first_ts=False):
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
        return (None)

    data = {}
    rows = cur.execute("select * from result where ts >= ?", (first_ts,))
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
        data[ts].append(row["comment"])

    return (data)


def game_result(data):
    """
    slackの検索ログからゲームの結果を返す

    Parameters
    ----------
    data : dict
        slackの検索ログ

    Returns
    -------
    matches : dict
        検索した結果
    """

    result = {}
    for i in range(len(data)):
        if "blocks" in data[i]:
            if data[i]["user"] in g.ignore_userid:  # 除外ユーザからのポストは集計対象から外す
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
                    p1_name = c.member.NameReplace(msg[0])
                    p2_name = c.member.NameReplace(msg[2])
                    p3_name = c.member.NameReplace(msg[4])
                    p4_name = c.member.NameReplace(msg[6])
                    result[ts] = [p1_name, msg[1], p2_name, msg[3], p3_name, msg[5], p4_name, msg[7], msg[8]]
                    g.logging.trace(f"{ts}: {result[ts]}")  # type: ignore

    if len(result) == 0:
        return (None)
    else:
        return (result)
