"""
libs/functions/search.py
"""

import logging
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Tuple

from dateutil.relativedelta import relativedelta

from cls.types import SlackSearchData
import libs.global_value as g
from libs.utils import formatter, validator

SlackSearchDict = dict[str, SlackSearchData]


def slack_messages(word: str) -> SlackSearchDict:
    """slackログからメッセージを検索して返す

    Args:
        word (str): 検索するワード

    Returns:
        SlackSearchDict: 検索した結果
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
    data: SlackSearchDict = {}
    for x in matches:
        data[x["ts"]] = {
            "channel_id": x["channel"].get("id", ""),
            "user_id": x.get("user", ""),
            "text": x.get("text", ""),
        }

    return (data)


def get_message_details(matches: dict) -> SlackSearchDict:
    """メッセージ詳細情報取得

    Args:
        matches (dict): 対象データ

    Returns:
        SlackSearchDict: 詳細情報追加データ
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


def for_slack_score() -> SlackSearchDict:
    """過去ログからスコア記録を検索して返す

    Returns:
        SlackSearchDict: 検索した結果
    """

    matches = slack_messages(g.cfg.search.keyword)

    # ゲーム結果の抽出
    for key in list(matches.keys()):
        detection = validator.pattern(matches[key].get("text", ""))
        if isinstance(detection, list):
            if matches[key].get("user_id", "") in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s (%s)", matches[key]["user_id"], detection)
                matches.pop(key)
                continue
            for i in range(0, 8, 2):
                g.params.update(unregistered_replace=False)  # 名前ブレを修正(ゲスト無効)
                detection[i] = formatter.name_replace(detection[i], False)
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


def for_slack_remarks() -> SlackSearchDict:
    """slackログからメモを検索して返す

    Returns:
        SlackSearchDict: 検索した結果
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
                matches[key]["remarks"].append((formatter.name_replace(name, False), matter))
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
