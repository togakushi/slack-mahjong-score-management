import logging
import re

from slack_sdk.errors import SlackApiError

import global_value as g
from lib import function as f


def call_chat_postMessage(**kwargs):
    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.msg.client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        logging.error(e)

    return (res)


def call_files_upload(**kwargs):
    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.msg.client.files_upload_v2(**kwargs)
    except SlackApiError as e:
        logging.error(e)

    return (res)


def post_message(message, ts=False):
    res = {}
    if not ts and g.msg.thread_ts:
        ts = g.msg.thread_ts

    if g.args.testcase:
        f.common.debug_out(message)
        res["ts"] = 0  # dummy
    else:
        res = call_chat_postMessage(
            channel=g.msg.channel_id,
            text=f"{message.strip()}",
            thread_ts=ts,
        )

    return (res)


def post_multi_message(msg, ts=False, summarize=True):
    if g.args.testcase:
        f.common.debug_out("", msg)
    else:
        if type(msg) is dict:
            if summarize:  # まとめてポスト
                key_list = list(msg.keys())
                post_msg = msg[key_list[0]]
                for i in key_list[1:]:
                    # 4000文字を超える直前までまとめる
                    if len((post_msg + msg[i])) < 4000:
                        post_msg += msg[i]
                    else:
                        post_message(post_msg, ts)
                        post_msg = msg[i]
                else:
                    post_message(post_msg, ts)
            else:  # そのままポスト
                for i in msg.keys():
                    post_message(msg[i], ts)
        else:
            post_message(msg, ts)


def post_text(event_ts, title, msg):
    # コードブロック修飾付きポスト
    if len(re.sub(r"\n+", "\n", f"{msg.strip()}").splitlines()) == 1:
        res = call_chat_postMessage(
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
        for i in range(len(post_msg)):
            res = call_chat_postMessage(
                channel=g.msg.channel_id,
                text=f"\n{title}\n\n```{post_msg[i].strip()}```",
                thread_ts=event_ts,
            )

    return (res)


def post_fileupload(title, file, ts=False):
    if not ts and g.msg.thread_ts:
        ts = g.msg.thread_ts

    if g.args.testcase:
        res = f.common.debug_out(title, file)
    else:
        res = call_files_upload(
            channel=g.msg.channel_id,
            title=title,
            file=file,
            thread_ts=ts,
            request_file_info=False,
        )

    return (res)


def slack_post(**kwargs):
    logging.debug(f"{kwargs}")
    headline = kwargs["headline"] if "headline" in kwargs else None
    message = kwargs["message"] if "message" in kwargs else None
    summarize = kwargs["summarize"] if "summarize" in kwargs else True
    file_list = kwargs["file_list"] if "file_list" in kwargs else {}

    # 見出しポスト
    res = post_message(headline)

    # 本文ポスト
    if file_list:
        for x in file_list.keys():
            post_fileupload(x, file_list[x], res["ts"])
    else:
        if message:
            post_multi_message(message, res["ts"], summarize)


def call_reactions_add(icon):
    """
    リアクションを付ける
    """

    res = g.msg.client.reactions_get(
        channel=g.msg.channel_id,
        timestamp=g.msg.event_ts,
    )

    # 既にリアクションが付いてるなら何もしない
    if "reactions" in res["message"]:
        for reaction in res["message"]["reactions"]:
            if reaction["name"] == g.cfg.setting.reaction_ok:
                if g.msg.bot_id in reaction["users"]:
                    return
            if reaction["name"] == g.cfg.setting.reaction_ng:
                if g.msg.bot_id in reaction["users"]:
                    return

    g.msg.client.reactions_add(
        channel=g.msg.channel_id,
        name=icon,
        timestamp=g.msg.event_ts,
    )


def call_reactions_remove():
    """
    botが付けたリアクションを外す
    """

    res = g.msg.client.reactions_get(
        channel=g.msg.channel_id,
        timestamp=g.msg.event_ts,
    )

    if "reactions" in res["message"]:
        for reaction in res["message"]["reactions"]:
            if reaction["name"] == g.cfg.setting.reaction_ok:
                if g.msg.bot_id in reaction["users"]:
                    g.msg.client.reactions_remove(
                        channel=g.msg.channel_id,
                        name=g.cfg.setting.reaction_ok,
                        timestamp=g.msg.event_ts,
                    )
            if reaction["name"] == g.cfg.setting.reaction_ng:
                if g.msg.bot_id in reaction["users"]:
                    g.msg.client.reactions_remove(
                        channel=g.msg.channel_id,
                        name=g.cfg.setting.reaction_ng,
                        timestamp=g.msg.event_ts,
                    )
