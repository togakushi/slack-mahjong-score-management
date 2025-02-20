import logging
import re

from slack_sdk.errors import SlackApiError

import lib.global_value as g
from lib import function as f


def call_chat_postMessage(**kwargs):
    """slackにメッセージをポストする

    Returns:
        SlackResponse: API response
    """

    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.app.client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        logging.critical(e)
        logging.error("kwargs=%s", kwargs)
        logging.error("opt: %s", vars(g.opt))
        logging.error("prm: %s", vars(g.prm))
        logging.error("msg: %s", vars(g.msg))

    return (res)


def call_files_upload(**kwargs):
    """slackにファイルをアップロードする

    Returns:
        SlackResponse: API response
    """

    res = None
    if not kwargs["thread_ts"]:
        kwargs.pop("thread_ts")
    try:
        res = g.app.client.files_upload_v2(**kwargs)
    except SlackApiError as e:
        logging.critical(e)
        logging.error("kwargs=%s", kwargs)
        logging.error("opt: %s", vars(g.opt))
        logging.error("prm: %s", vars(g.prm))
        logging.error("msg: %s", vars(g.msg))

    return (res)


def post_message(message, ts=False):
    """chat_postMessageに渡すパラメータを設定

    Args:
        message (str): ポストするメッセージ
        ts (bool, optional): スレッドに返す. Defaults to False.

    Returns:
        SlackResponse: API response
    """

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
    """メッセージを分割してポスト

    Args:
        msg (Union[dict, list]): ポストするメッセージ
        ts (bool, optional): スレッドに返す. Defaults to False.
        summarize (bool, optional): 可能な限り1つのブロックにまとめる. Defaults to True.
    """

    if g.args.testcase:
        f.common.debug_out("", msg)
    else:
        if type(msg) is dict:
            if summarize:  # まとめてポスト
                key_list = list(msg.keys())
                post_msg = msg[key_list[0]]
                for i in key_list[1:]:
                    # 3800文字を超える直前までまとめる
                    if len((post_msg + msg[i])) < 3800:
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
    """コードブロック修飾付きポスト

    Args:
        event_ts (str): スレッドに返す
        title (str): タイトル行
        msg (str): 本文

    Returns:
        SlackResponse: API response
    """

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
    """files_upload_v2に渡すパラメータを設定

    Args:
        title (str): タイトル行
        file (str): アップロードファイルパス
        ts (bool, optional): スレッドに返す. Defaults to False.

    Returns:
        SlackResponse: API response
    """

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
    """パラメータの内容によって呼び出すAPIを振り分ける
    """

    logging.debug(kwargs)
    headline = kwargs.get("headline")
    message = kwargs.get("message")
    summarize = kwargs.get("summarize", True)
    file_list = kwargs.get("file_list", {})

    # 見出しポスト
    res = post_message(headline)
    if res:
        ts = res.get("ts")
    else:
        ts = None

    # 本文ポスト
    if file_list:
        for x in file_list.keys():
            post_fileupload(x, file_list[x], ts)
    else:
        if message:
            post_multi_message(message, ts, summarize)


def call_reactions_add(icon, ch=None, ts=None):
    """リアクションを付ける

    Args:
        icon (str): 付けるリアクション
        ch (str, optional): チャンネルID. Defaults to None.
        ts (str, optional): メッセージのタイムスタンプ. Defaults to None.
    """

    if not ch:
        ch = g.msg.channel_id
    if not ts:
        ts = g.msg.event_ts

    try:
        res = g.app.client.reactions_add(
            channel=ch,
            name=icon,
            timestamp=ts,
        )
        logging.info(f"{ts=}, {ch=}, {icon=}, {res.validate()}")
    except SlackApiError as e:
        match e.response.get("error"):
            case "already_reacted":
                pass
            case _:
                logging.critical(e)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)
                logging.error("opt: %s", vars(g.opt))
                logging.error("prm: %s", vars(g.prm))
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
        logging.info(f"{ts=}, {ch=}, {icon=}, {res.validate()}")
    except SlackApiError as e:
        match e.response.get("error"):
            case "no_reaction":
                pass
            case _:
                logging.critical(e)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)
                logging.error("opt: %s", vars(g.opt))
                logging.error("prm: %s", vars(g.prm))
                logging.error("msg: %s", vars(g.msg))


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
    icon = []

    try:  # 削除済みメッセージはエラーになるので潰す
        res = g.app.client.reactions_get(channel=ch, timestamp=ts)
        logging.trace(res.validate())
    except SlackApiError:
        return (icon)

    if "reactions" in res["message"]:
        for reaction in res["message"]["reactions"]:
            if g.bot_id in reaction["users"]:
                icon.append(reaction["name"])

    logging.info("ch=%s, ts=%s, user=%s, icon=%s", ch, ts, g.bot_id, icon)
    return (icon)


def get_dm_channel_id(user_id):
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

    return (channel_id)


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
    res = {}

    try:
        res = g.app.client.conversations_replies(channel=ch, ts=ts)
        logging.trace(res.validate())
    except SlackApiError as e:
        logging.error(e)

    return (res)
