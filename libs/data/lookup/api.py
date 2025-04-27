"""
lib/data/lookup/api.py
"""

import logging

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g


def reactions_status(ch=None, ts=None):
    """botが付けたリアクションの種類を返す

    Args:
        ch (str, optional): チャンネルID. Defaults to None.
        ts (str, optional): メッセージのタイムスタンプ. Defaults to None.

    Returns:
        list: リアクション
    """

    ch = ch if ch else g.msg.channel_id
    ts = ts if ts else g.msg.event_ts
    icon: list = []

    try:  # 削除済みメッセージはエラーになるので潰す
        res = g.app.client.reactions_get(channel=ch, timestamp=ts)
        logging.trace(res.validate())  # type: ignore
    except SlackApiError:
        return icon

    if "reactions" in res["message"]:
        for reaction in res["message"]["reactions"]:
            if g.bot_id in reaction["users"]:
                icon.append(reaction["name"])

    logging.info("ch=%s, ts=%s, user=%s, icon=%s", ch, ts, g.bot_id, icon)
    return icon


def get_channel_id() -> str | None:
    """チャンネルIDを取得する

    Returns:
        str: チャンネルID
    """

    channel_id = None

    try:
        response = g.webclient.search_messages(
            query=f"in:{g.cfg.search.channel}",
            count=1,
        )
        messages: dict = response.get("messages", {})
        if messages.get("matches"):
            channel = messages["matches"][0]["channel"]
            if isinstance(g.cfg.search.channel, str):
                if channel["name"] in g.cfg.search.channel:
                    channel_id = channel["id"]
            else:
                channel_id = channel["id"]
    except SlackApiError as e:
        logging.error(e)

    return channel_id


def get_dm_channel_id(user_id: str) -> str | None:
    """DMのチャンネルIDを取得する

    Args:
        user_id (str): DMの相手

    Returns:
        str: チャンネルID
    """

    channel_id = None

    try:
        response = g.app.client.conversations_open(users=[user_id])
        channel_id = response["channel"]["id"]
    except SlackApiError as e:
        logging.error(e)

    return channel_id


def get_conversations(ch=None, ts=None):
    """スレッド情報の取得

    Args:
        ch (str, optional): チャンネルID. Defaults to None.
        ts (str, optional): メッセージのタイムスタンプ. Defaults to None.

    Returns:
        SlackResponse: API response
    """

    ch = ch if ch else g.msg.channel_id
    ts = ts if ts else g.msg.event_ts
    res: SlackResponse

    try:
        res = g.app.client.conversations_replies(channel=ch, ts=ts)
        logging.trace(res.validate())  # type: ignore
    except SlackApiError as e:
        logging.error(e)

    return res
