import logging
import re
from datetime import datetime

import regex_spm
from dateutil.relativedelta import relativedelta

import global_value as g
from lib import function as f


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
    class Regexes:
        keyword = g.cfg.search.keyword
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
    after = (datetime.now() - relativedelta(days=g.cfg.search.after)).strftime("%Y-%m-%d")
    query = f"{keyword} in:{channel} after:{after}"
    logging.info(f"{query=}")

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
        g.msg.parser_matches(data[i])

        if g.msg.user_id in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは集計対象から外す
            logging.info(f"skip: {data[i]}")
            continue

        # 結果報告フォーマットに一致しているポストの保存
        detection = f.search.pattern(g.msg.text)
        if detection:
            result[g.msg.event_ts] = data[i]
            logging.trace(f"{g.msg.event_ts}: {data[i]}")  # type: ignore

    if len(result) == 0:
        return (None)
    else:
        return (result)
