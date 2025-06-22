"""
libs/functions/search.py
"""

import logging
import re
from contextlib import closing
from typing import cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import SlackSearchData
from libs.utils import dbutil, formatter, validator

SlackSearchDict = dict[str, SlackSearchData]
DBSearchDict = dict[str, GameResult]


def slack_messages(word: str) -> SlackSearchDict:
    """slackログからメッセージを検索して返す

    Args:
        word (str): 検索するワード

    Returns:
        SlackSearchDict: 検索した結果
    """

    # 検索クエリ
    after = ExtDt(days=-g.cfg.search.after).format("ymd", "-")
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
    data: SlackSearchDict = cast(SlackSearchDict, {})
    for x in matches:
        if isinstance(x, dict):
            data[x["ts"]] = {
                "channel_id": str(cast(dict, x["channel"]).get("id", "")),
                "user_id": str(x.get("user", "")),
                "text": str(x.get("text", "")),
            }

    return data


def get_message_details(matches: SlackSearchDict) -> SlackSearchDict:
    """メッセージ詳細情報取得

    Args:
        matches (SlackSearchDict): 対象データ

    Returns:
        SlackSearchDict: 詳細情報追加データ
    """

    # 詳細情報取得
    for key, val in matches.items():
        res: dict = {}
        if isinstance(channel_id := val.get("channel_id"), str):
            conversations = g.app.client.conversations_replies(channel=channel_id, ts=key)
            if (msg := conversations.get("messages")):
                res = cast(dict, msg[0])
        else:
            continue

        if res:
            # 各種時間取得
            matches[key].update({"event_ts": res.get("ts")})  # イベント発生時間
            matches[key].update({"thread_ts": res.get("thread_ts")})  # スレッドの先頭
            matches[key].update({"edited_ts": cast(dict, res.get("edited", {})).get("ts")})  # 編集時間
            # リアクション取得
            reaction_ok, reaction_ng = reactions_list(res)
            matches[key].update({"reaction_ok": reaction_ok})
            matches[key].update({"reaction_ng": reaction_ng})
            # スレッド内フラグ
            if val.get("event_ts") == val.get("thread_ts") or val.get("thread_ts") is None:
                matches[key].update({"in_thread": False})
            else:
                matches[key].update({"in_thread": True})

    return matches


def for_slack_score() -> SlackSearchDict:
    """過去ログからスコア記録を検索して返す

    Returns:
        SlackSearchDict: 検索した結果
    """

    matches = slack_messages(g.cfg.search.keyword)

    # ゲーム結果の抽出
    g.params.update(unregistered_replace=False)  # ゲスト無効
    g.params.update(individual=True)  # チーム戦オフ
    for key in list(matches.keys()):
        detection = validator.pattern(matches[key].get("text", ""))
        if not detection.is_default():
            detection.set(ts=key)
            detection.calc()
            if matches[key].get("user_id", "") in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s (%s)", matches[key]["user_id"], detection)
                matches.pop(key)
                continue

            matches[key]["score"] = detection
            matches[key].pop("text")
        else:  # 不一致は破棄
            matches.pop(key)

    # 結果が無い場合は空の辞書を返して後続の処理をスキップ
    if not matches:
        return cast(SlackSearchDict, {})

    matches = get_message_details(matches)
    g.msg.channel_type = "search_messages"
    return matches


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
        return cast(SlackSearchDict, {})

    matches = get_message_details(matches)
    g.msg.channel_type = "search_messages"
    return matches


def for_db_score(first_ts: float | bool = False) -> DBSearchDict:
    """データベースからスコアを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        DBSearchDict: 検索した結果
    """

    if not first_ts:
        return {}

    data: DBSearchDict = {}
    with closing(dbutil.get_connection()) as conn:
        curs = conn.cursor()
        rows = curs.execute("select * from result where ts >= ?", (str(first_ts),))
        for row in rows.fetchall():
            ts = str(dict(row).get("ts", ""))
            result = GameResult(ts=ts)
            result.set(**dict(row))
            data[ts] = result

    return data


def for_db_remarks(first_ts: float | bool = False) -> list:
    """データベースからメモを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        list: 検索した結果
    """

    if not first_ts:
        return []

    # データベースからデータ取得
    data: list = []
    with closing(dbutil.get_connection()) as cur:
        # 記録済みメモ内容
        rows = cur.execute("select * from remarks where thread_ts>=?", (str(first_ts),))
        for row in rows.fetchall():
            data.append({
                "thread_ts": row["thread_ts"],
                "event_ts": row["event_ts"],
                "name": row["name"],
                "matter": row["matter"],
            })

    return data


def reactions_list(msg: dict) -> tuple[list, list]:
    """botが付けたリアクションを取得

    Args:
        msg (dict): メッセージ内容

    Returns:
        tuple[list, list]:
        - reaction_ok: okが付いているメッセージのタイムスタンプ
        - reaction_ng: ngが付いているメッセージのタイムスタンプ
    """

    reaction_ok: list = []
    reaction_ng: list = []

    if msg.get("reactions"):
        for reactions in msg.get("reactions", {}):
            if isinstance(reactions, dict) and g.bot_id in reactions.get("users", []):
                match reactions.get("name"):
                    case g.cfg.setting.reaction_ok:
                        reaction_ok.append(msg.get("ts"))
                    case g.cfg.setting.reaction_ng:
                        reaction_ng.append(msg.get("ts"))

    return (reaction_ok, reaction_ng)
