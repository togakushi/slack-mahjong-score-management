"""
integrations/slack/functions/reactions.py
"""

import logging

import libs.global_value as g
from cls.score import GameResult
from integrations import factory
from integrations.slack import api
from libs.data import lookup
from libs.functions import message


def score_verification(detection: GameResult, reactions_data: list | None = None) -> None:
    """素点合計をチェックしリアクションを付ける

    Args:
        detection (GameResult): スコアデータ
        reactions_data (list | None, optional): リアクションリスト. Defaults to None.
    """

    message_adapter = factory.get_message_adapter(g.selected_service)

    if not reactions_data:
        reactions_data = lookup.api.reactions_status()

    if detection.deposit:
        if g.cfg.setting.reaction_ok in reactions_data:
            api.reactions.call_reactions_remove(g.cfg.setting.reaction_ok)
        if g.cfg.setting.reaction_ng not in reactions_data:
            api.reactions.call_reactions_add(g.cfg.setting.reaction_ng)

        message_adapter.post_message(
            message.random_reply(message="invalid_score", rpoint_sum=detection.rpoint_sum()),
            g.msg.event_ts,
        )
    else:
        if g.cfg.setting.reaction_ng in reactions_data:
            api.reactions.call_reactions_remove(g.cfg.setting.reaction_ng)
        if g.cfg.setting.reaction_ok not in reactions_data:
            api.reactions.call_reactions_add(g.cfg.setting.reaction_ok)


def all_remove(delete_list: list):
    """すべてのリアクションを削除する

    Args:
        delete_list (list): 削除対象のタイムスタンプ
    """

    for ts in set(delete_list):
        for icon in lookup.api.reactions_status(ts=ts):
            api.reactions.call_reactions_remove(icon, ts=ts)
            logging.info("ts=%s, icon=%s", ts, icon)
