"""
integrations/slack/functions.py
"""

import copy
import logging
from typing import cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from integrations.protocols import MessageParserProtocol
from libs.functions import message

SlackSearchDict = dict[str, MessageParserProtocol]


def score_verification(detection: GameResult, m: MessageParserProtocol) -> None:
    """素点合計をチェックしリアクションを付ける

    Args:
        detection (GameResult): ゲーム結果
        m (MessageParserProtocol): メッセージデータ
    """

    api_adapter = factory.select_adapter(g.selected_service)
    reactions = api_adapter.reactions.status(ch=m.data.channel_id, ts=m.data.event_ts)

    if detection.deposit:
        if reactions.get("ok"):
            api_adapter.reactions.remove(icon=m.reaction_ok, ch=m.data.channel_id, ts=m.data.event_ts)
        if not reactions.get("ng"):
            api_adapter.reactions.append(icon=m.reaction_ng, ch=m.data.channel_id, ts=m.data.event_ts)

        m.post.message_type = "invalid_score"
        m.post.rpoint_sum = detection.rpoint_sum()
        m.post.message = message.random_reply(m)
        m.post.thread = True
        api_adapter.post_message(m)
    else:
        if not reactions.get("ok"):
            api_adapter.reactions.append(icon=m.reaction_ok, ch=m.data.channel_id, ts=m.data.event_ts)
        if reactions.get("ng"):
            api_adapter.reactions.remove(icon=m.reaction_ng, ch=m.data.channel_id, ts=m.data.event_ts)


def get_messages(word: str) -> SlackSearchDict:
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
    m = factory.select_parser(g.selected_service, **g.cfg.setting.to_dict())
    for x in matches:
        if isinstance(x, dict):
            tmp_m = copy.deepcopy(m)
            tmp_m.parser(x)
            data[x["ts"]] = tmp_m

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
        conversations = g.app.client.conversations_replies(channel=val.data.channel_id, ts=val.data.event_ts)
        if (msg := conversations.get("messages")):
            res = cast(dict, msg[0])
        else:
            continue

        if res:
            # 各種時間取得
            matches[key].data.event_ts = str(res.get("ts", "0"))  # イベント発生時間
            matches[key].data.thread_ts = str(res.get("thread_ts", "0"))  # スレッドの先頭
            matches[key].data.edited_ts = str(cast(dict, res.get("edited", {})).get("ts", "0"))  # 編集時間
            # リアクション取得
            matches[key].data.reaction_ok, matches[key].data.reaction_ng = get_reactions_list(res)

    return matches


def pickup_score() -> SlackSearchDict:
    """過去ログからスコア記録を検索して返す

    Returns:
        SlackSearchDict: 検索した結果
    """

    matches = get_messages(g.cfg.search.keyword)

    # ゲーム結果の抽出
    for key in list(matches.keys()):
        if matches[key].get_score(g.cfg.search.keyword):
            if matches[key].data.user_id in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s", matches[key].data.user_id)
                matches.pop(key)
                continue
        else:  # 不一致は破棄
            matches.pop(key)

    # 結果が無い場合は空の辞書を返して後続の処理をスキップ
    if not matches:
        return cast(SlackSearchDict, {})

    # イベント詳細取得
    matches = get_message_details(matches)

    return matches


def pickup_remarks() -> SlackSearchDict:
    """slackログからメモを検索して返す

    Returns:
        SlackSearchDict: 検索した結果
    """

    matches = get_messages(g.cfg.cw.remarks_word)

    # メモの抽出
    for key in list(matches.keys()):
        if matches[key].data.user_id in g.cfg.setting.ignore_userid:  # 除外ユーザからのポストは破棄
            logging.info("skip ignore user: %s", matches[key].data.user_id)
            matches.pop(key)
            continue

        if (remark := matches[key].get_remarks(g.cfg.cw.remarks_word)):
            matches[key].data.remarks = remark
        else:  # 不一致は破棄
            matches.pop(key)

    # 結果が無い場合は空の辞書を返して後続の処理をスキップ
    if not matches:
        return cast(SlackSearchDict, {})

    matches = get_message_details(matches)
    return matches


def get_reactions_list(msg: dict) -> tuple[list, list]:
    """botが付けたリアクションを取得

    Args:
        msg (dict): メッセージ内容

    Returns:
        tuple[list,list]:
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
