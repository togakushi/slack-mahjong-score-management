"""
integrations/slack/functions/message.py
"""

import logging
import re
from typing import Any, cast

from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.slack import api
from libs.utils import formatter


def post_message(msg: str, ts=False) -> SlackResponse | Any:
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
        formatter.debug_out(msg)
        res["ts"] = 0  # dummy
    else:
        res = api.post.call_chat_post_message(
            channel=g.msg.channel_id,
            text=f"{msg.strip()}",
            thread_ts=ts,
        )

    return res


def post_multi_message(msg: dict, ts: bool | None = False, summarize: bool = True) -> None:
    """メッセージを分割してポスト

    Args:
        msg (dict): ポストするメッセージ
        ts (bool, optional): スレッドに返す. Defaults to False.
        summarize (bool, optional): 可能な限り1つのブロックにまとめる. Defaults to True.
    """

    if g.args.testcase:
        formatter.debug_out("", msg)
    else:
        if isinstance(msg, dict):
            if summarize:  # まとめてポスト
                key_list = list(map(str, msg.keys()))
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


def post_text(event_ts: str, title: str, msg: str) -> SlackResponse | Any:
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
        res = api.post.call_chat_post_message(
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
            res = api.post.call_chat_post_message(
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

    res = api.post.call_files_upload(
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
    headline = str(kwargs.get("headline", ""))
    msg = kwargs.get("message")
    summarize = bool(kwargs.get("summarize", True))
    file_list = cast(dict, kwargs.get("file_list", {"dummy": ""}))

    # 見出しポスト
    if (res := post_message(headline)):
        ts = res.get("ts", False)
    else:
        ts = False

    # 本文ポスト
    for x in file_list:
        if (file_path := file_list.get(x)):
            post_fileupload(str(x), str(file_path), ts)
            msg = {}  # ファイルがあるメッセージは不要

    if msg:
        post_multi_message(msg, ts, summarize)
