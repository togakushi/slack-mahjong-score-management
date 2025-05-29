"""
libs/functions/slack_api.py
"""

import logging
import re
from typing import Any

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g
from libs.utils import formatter


def call_chat_post_message(**kwargs) -> SlackResponse | Any:
    """slackにメッセージをポストする

    Returns:
        SlackResponse | Any: API response
    """

    res = None
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


def post_message(message, ts=False) -> SlackResponse | Any:
    """chat_postMessageに渡すパラメータを設定

    Args:
        message (str): ポストするメッセージ
        ts (bool, optional): スレッドに返す. Defaults to False.

    Returns:
        SlackResponse | Any: API response
    """

    res: dict | Any = {}
    if not ts and g.msg.thread_ts:
        ts = g.msg.thread_ts

    if g.args.testcase:
        formatter.debug_out(message)
        res["ts"] = 0  # dummy
    else:
        res = call_chat_post_message(
            channel=g.msg.channel_id,
            text=f"{message.strip()}",
            thread_ts=ts,
        )

    return res


def post_multi_message(msg: dict | list, ts: bool | None = False, summarize: bool = True) -> None:
    """メッセージを分割してポスト

    Args:
        msg (Union[dict, list]): ポストするメッセージ
        ts (bool, optional): スレッドに返す. Defaults to False.
        summarize (bool, optional): 可能な限り1つのブロックにまとめる. Defaults to True.
    """

    if g.args.testcase:
        formatter.debug_out("", msg)
    else:
        if isinstance(msg, dict):
            if summarize:  # まとめてポスト
                key_list = list(msg.keys())
                post_msg = msg[key_list[0]]
                for i in key_list[1:]:
                    if len((post_msg + msg[i])) < 3800:  # 3800文字を超える直前までまとめる
                        post_msg += msg[i]
                    else:
                        post_message(post_msg, ts)
                        post_msg = msg[i]
                post_message(post_msg, ts)
            else:  # そのままポスト
                for i in msg.keys():
                    post_message(msg[i], ts)
        else:
            post_message(msg, ts)


def post_text(event_ts, title, msg) -> SlackResponse | Any:
    """コードブロック修飾付きポスト

    Args:
        event_ts (str): スレッドに返す
        title (str): タイトル行
        msg (str): 本文

    Returns:
        SlackResponse | Any: API response
    """

    # コードブロック修飾付きポスト
    if len(re.sub(r"\n+", "\n", f"{msg.strip()}").splitlines()) == 1:
        res = call_chat_post_message(
            channel=g.msg.channel_id,
            text=f"{title}\n{msg.strip()}",
            thread_ts=event_ts,
        )
    else:
        # ポスト予定のメッセージをstep行単位のブロックに分割
        step = 50
        post_msg = []
        for count in range(int(len(msg.splitlines()) / step) + 1):
            post_msg.append(
                "\n".join(msg.splitlines()[count * step:(count + 1) * step])
            )

        # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
        if len(post_msg) > 1 and step / 2 > len(post_msg[count].splitlines()):
            post_msg[count - 1] += "\n" + post_msg.pop(count)

        # ブロック単位でポスト
        for _, val in enumerate(post_msg):
            res = call_chat_post_message(
                channel=g.msg.channel_id,
                text=f"\n{title}\n\n```{val.strip()}```",
                thread_ts=event_ts,
            )

    return res


def post_fileupload(title: str, file: str | bool, ts: str | bool = False) -> SlackResponse | None:
    """files_upload_v2に渡すパラメータを設定

    Args:
        title (str): タイトル行
        file (str): アップロードファイルパス
        ts (str | bool, optional): スレッドに返す. Defaults to False.

    Returns:
        SlackResponse | None: 結果
    """

    if g.args.testcase:
        formatter.debug_out(title, file)
        return None

    if not ts and g.msg.thread_ts:
        ts = g.msg.thread_ts

    res = call_files_upload(
        channel=g.msg.channel_id,
        title=title,
        file=file,
        thread_ts=ts,
        request_file_info=False,
    )

    return res


def slack_post(**kwargs):
    """パラメータの内容によって呼び出すAPIを振り分ける"""
    logging.debug(kwargs)
    headline = kwargs.get("headline")
    message = kwargs.get("message")
    summarize = kwargs.get("summarize", True)
    file_list = kwargs.get("file_list", {})

    # 見出しポスト
    res = post_message(headline)
    if res:
        ts = res.get("ts", False)
    else:
        ts = False

    # 本文ポスト
    if file_list:
        for x in file_list.keys():
            post_fileupload(str(x), str(file_list[x]), ts)
    else:
        if message:
            post_multi_message(message, ts, summarize)


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


def call_reactions_remove(icon, ch=None, ts=None):
    """リアクションを外す

    Args:
        icon (str): 外すリアクション
        ch (str, optional): チャンネルID. Defaults to None.
        ts (str, optional): メッセージのタイムスタンプ. Defaults to None.
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
