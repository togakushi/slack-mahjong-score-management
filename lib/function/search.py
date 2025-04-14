"""
lib/function/search.py
"""

import logging
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Tuple

from dateutil.relativedelta import relativedelta

import lib.global_value as g
from cls.types import SlackSearchDict
from lib import command as c
from lib import function as f


def pattern(text: str) -> list | bool:
    """成績記録用フォーマットチェック

    Args:
        text (str): slackにポストされた内容

    Returns:
        Tuple[list,bool]:
            - list: フォーマットに一致すればスペース区切りの名前と素点のペア
            - False: メッセージのパースに失敗した場合
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

    text = "".join(text.split())

    # パターンマッチング
    pattern1 = re.compile(
        rf"^({g.cfg.search.keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern2 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({g.cfg.search.keyword})$"
    )
    pattern3 = re.compile(
        rf"^({g.cfg.search.keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern4 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({g.cfg.search.keyword})\((.+?)\)$"
    )

    msg: list | bool
    match text:
        case text if pattern1.findall(text):
            m = pattern1.findall(text)[0]
            msg = [m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], None]
        case text if pattern2.findall(text):
            m = pattern2.findall(text)[0]
            msg = [m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], None]
        case text if pattern3.findall(text):
            m = pattern3.findall(text)[0]
            msg = [m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[1]]
        case text if pattern4.findall(text):
            m = pattern4.findall(text)[0]
            msg = [m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[9]]
        case _:
            msg = False

    return (msg)


def slack_messages(word: str) -> dict[str, SlackSearchDict]:
    """slackログからメッセージを検索して返す

    Args:
        word (str): 検索するワード

    Returns:
        dict[str, SlackSearchDict]: 検索した結果
    """

    # 検索クエリ
    after = (datetime.now() - relativedelta(days=g.cfg.search.after)).strftime("%Y-%m-%d")
    query = f"{word} in:{g.cfg.search.channel} after:{after}"
    logging.info("query=%s", query)

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

    # 必要なデータだけ辞書に格納
    data: dict[str, SlackSearchDict] = {}
    for x in matches:
        data[x["ts"]] = {
            "channel_id": x["channel"].get("id", ""),
            "user_id": x.get("user", ""),
            "text": x.get("text", ""),
        }

    return (data)


def get_message_details(matches: dict) -> dict[str, SlackSearchDict]:
    """メッセージ詳細情報取得

    Args:
        matches (dict): 対象データ

    Returns:
        dict[str,SlackSearchDict]: 詳細情報追加データ
    """

    # 詳細情報取得
    for key, val in matches.items():
        conversations = g.app.client.conversations_replies(
            channel=val.get("channel_id"),
            ts=key,
        )
        msg: list = conversations.get("messages", [])

        # 各種時間取得
        if msg[0].get("ts"):  # イベント発生時間
            val["event_ts"] = msg[0]["ts"]
        if msg[0].get("thread_ts"):  # スレッドの先頭
            val["thread_ts"] = msg[0]["thread_ts"]
        else:
            val["thread_ts"] = None
        if msg[0].get("edited"):  # 編集時間
            val["edited_ts"] = msg[0]["edited"]["ts"]
        else:
            val["edited_ts"] = None

        # リアクション取得
        reaction_ok, reaction_ng = reactions_list(msg[0])
        val["reaction_ok"] = reaction_ok
        val["reaction_ng"] = reaction_ng

        # スレッド内フラグ
        if val.get("event_ts") == val.get("thread_ts") or val.get("thread_ts") is None:
            val["in_thread"] = False
        else:
            val["in_thread"] = True

        matches[key].update(val)

    return (matches)


def for_slack_score() -> dict[str, SlackSearchDict]:
    """過去ログからスコア記録を検索して返す

    Returns:
        dict[str, SlackSearchDict]: 検索した結果
    """

    matches = slack_messages(g.cfg.search.keyword)

    # ゲーム結果の抽出
    for key in list(matches.keys()):
        detection = f.search.pattern(matches[key].get("text", ""))
        if isinstance(detection, list):
            if matches[key].get("user_id", "") in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s (%s)", matches[key]["user_id"], detection)
                matches.pop(key)
                continue
            for i in range(0, 8, 2):
                g.params.update(unregistered_replace=False)  # 名前ブレを修正(ゲスト無効)
                detection[i] = c.member.name_replace(detection[i], False)
            matches[key]["score"] = detection
            matches[key].pop("text")
        else:  # 不一致は破棄
            matches.pop(key)

    # 結果が無い場合は空の辞書を返して後続の処理をスキップ
    if not matches:
        return ({})

    matches = get_message_details(matches)
    g.msg.channel_type = "search_messages"
    return (matches)


def for_slack_remarks() -> dict[str, SlackSearchDict]:
    """slackログからメモを検索して返す

    Returns:
        dict[str, SlackSearchDict]: 検索した結果
    """

    matches = slack_messages(g.cfg.cw.remarks_word)

    # メモの抽出
    for key in list(matches.keys()):
        if re.match(rf"^{g.cfg.cw.remarks_word}", matches[key].get("text", "")):  # キーワードが先頭に存在するかチェック
            text = matches[key]["text"].replace(g.cfg.cw.remarks_word, "").strip().split()
            if matches[key].get("user_id", "") in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s, (%s)", matches[key]["user_id"], text)
                matches.pop(key)
                continue
            matches[key]["remarks"] = []
            g.params.update(unregistered_replace=False)  # 名前ブレを修正(ゲスト無効)
            for name, matter in zip(text[0::2], text[1::2]):
                matches[key]["remarks"].append((c.member.name_replace(name, False), matter))
            matches[key].pop("text")
        else:  # 不一致は破棄
            matches.pop(key)

    # 結果が無い場合は空の辞書を返して後続の処理をスキップ
    if not matches:
        return ({})

    matches = get_message_details(matches)
    g.msg.channel_type = "search_messages"
    return (matches)


def for_db_score(first_ts: float | bool = False) -> dict:
    """データベースからスコアを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        dict: 検索した結果
    """

    if not first_ts:
        return ({})

    data: dict = {}
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row
        curs = cur.cursor()

        rows = curs.execute("select * from result where ts >= ?", (str(first_ts),))
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


def for_db_remarks(first_ts: float | bool = False) -> list:
    """データベースからメモを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        list: 検索した結果
    """

    if not first_ts:
        return ([])

    # データベースからデータ取得
    data: list = []
    with closing(sqlite3.connect(g.cfg.db.database_file, detect_types=sqlite3.PARSE_DECLTYPES)) as cur:
        cur.row_factory = sqlite3.Row

        # 記録済みメモ内容
        rows = cur.execute("select * from remarks where thread_ts>=?", (str(first_ts),))
        for row in rows.fetchall():
            data.append({
                "thread_ts": row["thread_ts"],
                "event_ts": row["event_ts"],
                "name": row["name"],
                "matter": row["matter"],
            })

    return (data)


def reactions_list(msg: Any) -> Tuple[list, list]:
    """botが付けたリアクションを取得

    Args:
        msg (Any): メッセージ内容

    Returns:
        Tuple[list, list]:
            - reaction_ok: okが付いているメッセージのタイムスタンプ
            - reaction_ng: ngが付いているメッセージのタイムスタンプ
    """

    reaction_ok: list = []
    reaction_ng: list = []

    if msg.get("reactions"):
        for reactions in msg.get("reactions"):
            if g.bot_id in reactions.get("users"):
                match reactions.get("name"):
                    case g.cfg.setting.reaction_ok:
                        reaction_ok.append(msg.get("ts"))
                    case g.cfg.setting.reaction_ng:
                        reaction_ng.append(msg.get("ts"))

    return (reaction_ok, reaction_ng)


def search_range(target_list: list) -> dict:
    """検索範囲取得

    Args:
        target_list (list): 日付

    Returns:
        dict: 取得情報
            - starttime: 検索開始日時
            - endtime: 検索終了日次
            - onday: 終了日時（日を跨がない）
    """

    day: list = []
    for x in target_list:
        day.extend(g.search_word.range(x))

    search_first = min(day)
    search_last = max(day) + relativedelta(days=1, hour=12)
    search_onday = max(day)

    return ({
        "starttime": search_first.replace(hour=12, minute=0, second=0, microsecond=0),
        "endtime": search_last.replace(hour=11, minute=59, second=59, microsecond=999999),
        "onday": search_onday.replace(hour=23, minute=59, second=59, microsecond=999999),
    })
