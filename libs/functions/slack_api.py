"""
libs/functions/slack_api.py
"""

import logging
from typing import cast

import libs.global_value as g
from cls.score import GameResult
from libs.api import slack
from libs.data import lookup
from libs.functions import message


def slack_post(**kwargs):
    """パラメータの内容によって呼び出すAPIを振り分ける"""

    logging.debug(kwargs)
    headline = str(kwargs.get("headline", ""))
    msg = kwargs.get("message")
    summarize = bool(kwargs.get("summarize", True))
    file_list = cast(dict, kwargs.get("file_list", {"dummy": ""}))

    # 見出しポスト
    if (res := slack.post.post_message(headline)):
        ts = res.get("ts", False)
    else:
        ts = False

    # 本文ポスト
    for x in file_list:
        if (file_path := file_list.get(x)):
            slack.post.post_fileupload(str(x), str(file_path), ts)
            msg = {}  # ファイルがあるメッセージは不要

    if msg:
        slack.post.post_multi_message(msg, ts, summarize)


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
            slack.reactions.call_reactions_remove(g.cfg.setting.reaction_ok)
        if g.cfg.setting.reaction_ng not in reactions_data:
            slack.reactions.call_reactions_add(g.cfg.setting.reaction_ng)

        slack.post.post_message(
            message.random_reply(message="invalid_score", rpoint_sum=detection.rpoint_sum()),
            g.msg.event_ts,
        )
    else:
        if g.cfg.setting.reaction_ng in reactions_data:
            slack.reactions.call_reactions_remove(g.cfg.setting.reaction_ng)
        if g.cfg.setting.reaction_ok not in reactions_data:
            slack.reactions.call_reactions_add(g.cfg.setting.reaction_ok)
