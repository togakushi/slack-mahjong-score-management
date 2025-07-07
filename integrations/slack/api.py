"""
integrations/slack/api.py
"""

import logging
from typing import Any, cast

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g


def call_chat_post_message(**kwargs) -> SlackResponse:
    """slackにメッセージをポストする

    Returns:
        SlackResponse: API response
    """

    res = cast(SlackResponse, {})
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.app.client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        logging.critical(e)
        logging.error("kwargs=%s", kwargs)
        logging.error("msg: %s", vars(g.msg))

    return res


def call_files_upload(**kwargs) -> SlackResponse | Any:
    """slackにファイルをアップロードする

    Returns:
        SlackResponse | Any: API response
    """

    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.app.client.files_upload_v2(**kwargs)
    except SlackApiError as e:
        logging.critical(e)
        logging.error("kwargs=%s", kwargs)
        logging.error("msg: %s", vars(g.msg))

    return res


def call_reactions_add(icon: str, ch: str | None = None, ts: str | None = None):
    """リアクションを付ける

    Args:
        icon (str): 付けるリアクション
        ch (str | None, optional): チャンネルID. Defaults to None.
        ts (str | None, optional): メッセージのタイムスタンプ. Defaults to None.
    """

    if not ch:
        ch = g.msg.channel_id
    if not ts:
        ts = g.msg.event_ts

    try:
        res: SlackResponse = g.app.client.reactions_add(
            channel=str(ch),
            name=icon,
            timestamp=str(ts),
        )
        logging.info("ts=%s, ch=%s, icon=%s, %s", ts, ch, icon, res.validate())
    except SlackApiError as e:
        match e.response.get("error"):
            case "already_reacted":
                pass
            case _:
                logging.critical(e)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)
                logging.error("msg: %s", vars(g.msg))


def call_reactions_remove(icon: str, ch: str | None = None, ts: str | None = None):
    """リアクションを外す

    Args:
        icon (str): 外すリアクション
        ch (str | None, optional): チャンネルID. Defaults to None.
        ts (str | None, optional): メッセージのタイムスタンプ. Defaults to None.
    """

    if not ch:
        ch = g.msg.channel_id
    if not ts:
        ts = g.msg.event_ts

    try:
        res = g.app.client.reactions_remove(
            channel=ch,
            name=icon,
            timestamp=ts,
        )
        logging.info("ts=%s, ch=%s, icon=%s, %s", ts, ch, icon, res.validate())
    except SlackApiError as e:
        match e.response.get("error"):
            case "no_reaction":
                pass
            case _:
                logging.critical(e)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)
                logging.error("msg: %s", vars(g.msg))
