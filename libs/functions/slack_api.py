"""
libs/functions/slack_api.py
"""

import logging
import re
from typing import Any, cast

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g
from cls.score import GameResult
from libs.data import lookup
from libs.functions import message
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
        formatter.debug_out(message)
        res["ts"] = 0  # dummy
    else:
        res = call_chat_post_message(
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


def score_reactions(detection: GameResult, reactions_data: list | None = None) -> None:
    """素点合計をチェックしリアクションを付ける

    Args:
        detection (GameResult): スコアデータ
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    if not reactions_data:
        reactions_data = lookup.api.reactions_status()

    if detection.deposit:
        if g.cfg.setting.reaction_ok in reactions_data:
            call_reactions_remove(g.cfg.setting.reaction_ok)
        if g.cfg.setting.reaction_ng not in reactions_data:
            call_reactions_add(g.cfg.setting.reaction_ng)

        post_message(
            message.random_reply(message="invalid_score", rpoint_sum=detection.rpoint_sum()),
            g.msg.event_ts,
        )
    else:
        if g.cfg.setting.reaction_ng in reactions_data:
            call_reactions_remove(g.cfg.setting.reaction_ng)
        if g.cfg.setting.reaction_ok not in reactions_data:
            call_reactions_add(g.cfg.setting.reaction_ok)


def all_remove_reactions(delete_list: list):
    """すべてのリアクションを削除する

    Args:
        delete_list (list): 削除対象のタイムスタンプ
    """

    for ts in set(delete_list):
        for icon in lookup.api.reactions_status(ts=ts):
            call_reactions_remove(icon, ts=ts)
            logging.info("ts=%s, icon=%s", ts, icon)
