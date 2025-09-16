"""
integrations/slack/api.py
"""

import logging
from typing import Any, cast

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.slack import config


def call_chat_post_message(**kwargs) -> SlackResponse:
    """slackにメッセージをポストする

    Returns:
        SlackResponse: API response
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    res = cast(SlackResponse, {})
    if kwargs["thread_ts"] == "0":
        kwargs.pop("thread_ts")

    try:
        res = g.app_config.appclient.chat_postMessage(**kwargs)
    except SlackApiError as err:
        logging.critical(err)
        logging.error("kwargs=%s", kwargs)

    return res


def call_files_upload(**kwargs) -> SlackResponse | Any:
    """slackにファイルをアップロードする

    Returns:
        SlackResponse | Any: API response
    """

    g.app_config = cast(config.AppConfig, g.app_config)
    res = None

    if kwargs.get("thread_ts", "0") == "0":
        kwargs.pop("thread_ts")

    try:
        res = g.app_config.appclient.files_upload_v2(**kwargs)
    except SlackApiError as err:
        logging.critical(err)
        logging.error("kwargs=%s", kwargs)

    return res


def call_reactions_add(icon: str, ch: str, ts: str):
    """リアクションを付ける

    Args:
        icon (str): 付けるリアクション
        ch (str): チャンネルID
        ts (str): メッセージのタイムスタンプ
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    if not all([icon, ch, ts]):
        logging.warning("deficiency: ts=%s, ch=%s, icon=%s", ts, ch, icon)
        return

    try:
        res: SlackResponse = g.app_config.appclient.reactions_add(
            channel=str(ch),
            name=icon,
            timestamp=str(ts),
        )
        logging.info("ts=%s, ch=%s, icon=%s, %s", ts, ch, icon, res.validate())
    except SlackApiError as err:
        match cast(dict, err.response).get("error"):
            case "already_reacted":
                pass
            case _:
                logging.critical(err)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)


def call_reactions_remove(icon: str, ch: str, ts: str):
    """リアクションを外す

    Args:
        icon (str): 外すリアクション
        ch (str): チャンネルID
        ts (str): メッセージのタイムスタンプ
    """

    g.app_config = cast(config.AppConfig, g.app_config)

    if not all([icon, ch, ts]):
        logging.warning("deficiency: ts=%s, ch=%s, icon=%s", ts, ch, icon)
        return

    try:
        res = g.app_config.appclient.reactions_remove(
            channel=ch,
            name=icon,
            timestamp=ts,
        )
        logging.info("ch=%s, ts=%s, icon=%s, %s", ch, ts, icon, res.validate())
    except SlackApiError as err:
        match cast(dict, err.response).get("error"):
            case "no_reaction":
                pass
            case "message_not_found":
                pass
            case _:
                logging.critical(err)
                logging.critical("ch=%s, ts=%s, icon=%s", ch, ts, icon)
