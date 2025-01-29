import logging
import re
import sqlite3
from contextlib import closing
from datetime import datetime

import regex_spm
from dateutil.relativedelta import relativedelta

import global_value as g
from lib import command as c
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


def for_slack():
    """
    過去ログからゲーム結果を検索して返す

    Returns
    -------
    data : dict
        検索した結果
    """

    g.opt.unregistered_replace = False  # ゲスト無効

    # 検索クエリ
    after = (datetime.now() - relativedelta(days=g.cfg.search.after)).strftime("%Y-%m-%d")
    query = f"{g.cfg.search.keyword} in:{g.cfg.search.channel} after:{after}"
    logging.info(f"{query=}")

    # データ取得
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

    # ゲーム結果の抽出
    data = {}
    for x in matches:
        user_id = x.get("user")
        if user_id in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは対象から外す
            logging.info(f"skip ignore user: {user_id}")
        else:
            detection = f.search.pattern(x.get("text"))
            if detection:
                for i in range(0, 8, 2):
                    detection[i] = c.member.name_replace(detection[i], False)

                data[x["ts"]] = {
                    "channel_id": x["channel"].get("id"),
                    "user_id": user_id,
                    "score": detection,
                    "event_ts": [],
                    "remarks": [],
                    "in_thread": False,
                    "reaction_ok": [],
                    "reaction_ng": [],
                }
    if not data:
        return (None)

    for thread_ts in data.keys():
        conversations = g.app.client.conversations_replies(
            channel=data[thread_ts].get("channel_id"),
            ts=thread_ts,
        )

        msg = conversations.get("messages")
        _ok, _ng = reactions_list(msg[0])
        data[thread_ts]["reaction_ok"] += _ok
        data[thread_ts]["reaction_ng"] += _ng

        if msg[0].get("ts") == msg[0].get("thread_ts") or msg[0].get("thread_ts") is None:
            if len(msg) >= 1:  # スレッド内探索
                for x in msg[1:]:
                    if re.match(rf"^{g.cfg.cw.remarks_word}", x.get("text")):  # 追加メモ
                        text = x.get("text").replace(g.cfg.cw.remarks_word, "").strip().split()
                        event_ts = x.get("ts")

                        _ok, _ng = reactions_list(x)
                        data[thread_ts]["reaction_ok"] += _ok
                        data[thread_ts]["reaction_ng"] += _ng

                        for name, matter in zip(text[0::2], text[1::2]):
                            data[thread_ts]["event_ts"].append(event_ts)
                            data[thread_ts]["remarks"].append((name, matter))
        else:
            data[thread_ts].update(in_thread=True)

    return (data)


def for_database(first_ts=False):
    """
    データベースからスコアを検索して返す

    Parameters
    ----------
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
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        curs = cur.cursor()

        rows = curs.execute("select * from result where ts >= ?", (first_ts,))
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


def for_db_remarks(first_ts=False):
    """
    データベースからメモを検索して返す

    Parameters
    ----------
    first_ts: float
        検索を開始する時刻

    Returns
    -------
    data : list
        検索した結果
    """

    if not first_ts:
        return (None)

    # データベースからデータ取得
    data = []
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row

        # 記録済みメモ内容
        rows = cur.execute("select * from remarks where thread_ts>=?", (first_ts,))
        for row in rows.fetchall():
            data.append({
                "thread_ts": row["thread_ts"],
                "event_ts": row["event_ts"],
                "name": row["name"],
                "matter": row["matter"],
            })

    return (data)


def reactions_list(msg):
    """
    botが付けたリアクションを取得
    """

    reaction_ok = []
    reaction_ng = []

    if msg.get("reactions"):
        for reactions in msg.get("reactions"):
            if g.bot_id in reactions.get("users"):
                match reactions.get("name"):
                    case g.cfg.setting.reaction_ok:
                        reaction_ok.append(msg.get("ts"))
                    case g.cfg.setting.reaction_ng:
                        reaction_ng.append(msg.get("ts"))

    return (reaction_ok, reaction_ng)
