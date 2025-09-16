"""
integrations/slack/functions.py
"""

import logging
from typing import cast

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.protocols import MessageParserProtocol
from integrations.slack import adapter, config, parser
from libs.functions import message


def score_verification(detection: GameResult, m: MessageParserProtocol) -> None:
    """素点合計をチェックしリアクションを付ける

    Args:
        detection (GameResult): ゲーム結果
        m (MessageParserProtocol): メッセージデータ
    """

    g.app_config = cast(config.AppConfig, g.app_config)
    api_adapter = adapter.SlackAPI()

    reactions = api_adapter.reactions.status(
        ch=m.data.channel_id,
        ts=m.data.event_ts,
        ok=g.app_config.reaction_ok,
        ng=g.app_config.reaction_ng,
    )
    status_flg: bool = True  # リアクション最終状態(True: OK, False: NG)
    m.post.message = {}

    # 素点合計チェック
    if detection.deposit:
        status_flg = False
        m.post.rpoint_sum = detection.rpoint_sum()
        m.post.ts = m.data.event_ts
        m.post.message.update({"0": message.random_reply(m, "invalid_score", False)})

    # プレイヤー名重複チェック
    if len(set(detection.to_list())) != 4:
        status_flg = False
        m.post.ts = m.data.event_ts
        m.post.message.update({"1": message.random_reply(m, "same_player", False)})

    # リアクション処理
    if status_flg:  # NGを外してOKを付ける
        if not reactions.get("ok"):
            api_adapter.reactions.append(icon=g.app_config.reaction_ok, ch=m.data.channel_id, ts=m.data.event_ts)
        if reactions.get("ng"):
            api_adapter.reactions.remove(icon=g.app_config.reaction_ng, ch=m.data.channel_id, ts=m.data.event_ts)
    else:  # OKを外してNGを付ける
        if reactions.get("ok"):
            api_adapter.reactions.remove(icon=g.app_config.reaction_ok, ch=m.data.channel_id, ts=m.data.event_ts)
        if not reactions.get("ng"):
            api_adapter.reactions.append(icon=g.app_config.reaction_ng, ch=m.data.channel_id, ts=m.data.event_ts)


def get_messages(word: str, m: MessageParserProtocol) -> list[MessageParserProtocol]:
    """slackログからメッセージを検索して返す

    Args:
        word (str): 検索するワード

    Returns:
        list[MessageParserProtocol]: 検索した結果
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    # 検索クエリ
    after = ExtDt(days=-g.app_config.search_after).format("ymd", "-")
    query = f"{word} in:{g.app_config.search_channel} after:{after}"
    logging.info("query=%s", query)

    # データ取得
    response = g.app_config.webclient.search_messages(
        query=query,
        sort="timestamp",
        sort_dir="asc",
        count=100
    )
    matches = response["messages"]["matches"]  # 1ページ目
    for p in range(2, response["messages"]["paging"]["pages"] + 1):
        response = g.app_config.webclient.search_messages(
            query=query,
            sort="timestamp",
            sort_dir="asc",
            count=100,
            page=p
        )
        matches += response["messages"]["matches"]  # 2ページ目以降

    # 必要なデータだけ辞書に格納
    data: list[MessageParserProtocol] = []
    for x in matches:
        if isinstance(x, dict):
            m = parser.MessageParser()
            m.parser(x)
            data.append(m)

    return data


def get_message_details(matches: list[MessageParserProtocol]) -> list[MessageParserProtocol]:
    """メッセージ詳細情報取得

    Args:
        matches (list[MessageParserProtocol]): 対象データ

    Returns:
        list[MessageParserProtocol]: 詳細情報追加データ
    """

    g.app_config = cast(config.AppConfig, g.app_config)
    new_matches: list[MessageParserProtocol] = []

    # 詳細情報取得
    for key in matches:
        conversations = g.app_config.appclient.conversations_replies(channel=key.data.channel_id, ts=key.data.event_ts)
        if (msg := conversations.get("messages")):
            res = cast(dict, msg[0])
        else:
            continue

        if res:
            # 各種時間取得
            key.data.event_ts = str(res.get("ts", "0"))  # イベント発生時間
            key.data.thread_ts = str(res.get("thread_ts", "0"))  # スレッドの先頭
            key.data.edited_ts = str(cast(dict, res.get("edited", {})).get("ts", "0"))  # 編集時間
            # リアクション取得
            key.data.reaction_ok, key.data.reaction_ng = get_reactions_list(res)

        new_matches.append(key)

    return new_matches


def pickup_score(m: MessageParserProtocol) -> list[MessageParserProtocol]:
    """過去ログからスコア記録を検索して返す

    Returns:
        list[MessageParserProtocol]: 検索した結果
    """

    g.app_config = cast(config.AppConfig, g.app_config)
    score_matches: list[MessageParserProtocol] = []

    # ゲーム結果の抽出
    for match in get_messages(g.cfg.setting.keyword, m):
        if match.get_score(g.cfg.setting.keyword):
            if match.data.user_id in g.app_config.ignore_userid:  # 除外ユーザからのポストは破棄
                logging.info("skip ignore user: %s", match.data.user_id)
                continue

            score_matches.append(match)

    # イベント詳細取得
    if score_matches:
        return get_message_details(score_matches)
    return score_matches


def pickup_remarks(m: MessageParserProtocol) -> list[MessageParserProtocol]:
    """slackログからメモを検索して返す

    Returns:
        list[MessageParserProtocol]: 検索した結果
    """

    g.app_config = cast(config.AppConfig, g.app_config)
    remarks_matches: list[MessageParserProtocol] = []

    # メモの抽出
    for match in get_messages(g.cfg.setting.remarks_word, m):
        if match.data.user_id in g.app_config.ignore_userid:  # 除外ユーザからのポストは破棄
            logging.info("skip ignore user: %s", match.data.user_id)
            continue

        if (remark := match.get_remarks(g.cfg.setting.remarks_word)):
            match.data.remarks = remark
        else:  # 不一致は破棄
            continue

        remarks_matches.append(match)

    # イベント詳細取得
    if remarks_matches:
        return get_message_details(remarks_matches)
    return remarks_matches


def get_reactions_list(msg: dict) -> tuple[list, list]:
    """botが付けたリアクションを取得

    Args:
        msg (dict): メッセージ内容

    Returns:
        tuple[list,list]:
        - reaction_ok: okが付いているメッセージのタイムスタンプ
        - reaction_ng: ngが付いているメッセージのタイムスタンプ
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    reaction_ok: list = []
    reaction_ng: list = []

    if msg.get("reactions"):
        for reactions in msg.get("reactions", {}):
            if isinstance(reactions, dict) and g.app_config.bot_id in reactions.get("users", []):
                match reactions.get("name"):
                    case g.app_config.reaction_ok:
                        reaction_ok.append(msg.get("ts"))
                    case g.app_config.reaction_ng:
                        reaction_ng.append(msg.get("ts"))

    return (reaction_ok, reaction_ng)
