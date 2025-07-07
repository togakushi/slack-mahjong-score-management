"""
integrations/slack/api/post.py
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
