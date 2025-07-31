"""
libs/functions/message.py
"""

import logging
import random
import textwrap
from configparser import ConfigParser
from typing import cast

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict
from integrations.protocols import MessageParserProtocol
from libs.functions import compose


def random_reply(m: MessageParserProtocol):
    """メッセージをランダムに返す

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    correct_score = g.cfg.mahjong.origin_point * 4  # 配給原点
    rpoint_diff = abs(correct_score - m.post.rpoint_sum)

    default_message_type = {
        "invalid_argument": "使い方が間違っています。",
        "no_hits": "{start} ～ {end} に≪{keyword}≫はありません。",
        "no_target": "集計対象データがありません。",
        "invalid_score": "素点合計：{rpoint_sum}\n点数差分：{rpoint_diff}",
        "restricted_channel": "<@{user_id}> この投稿はデータベースに反映されません。",
        "inside_thread": "<@{user_id}> スレッド内から成績登録はできません。",
        "same_player": "同名のプレイヤーがいます。",
    }

    msg = default_message_type.get(m.post.message_type, "invalid_argument")

    if cast(ConfigParser, getattr(g.cfg, "_parser")).has_section("custom_message"):
        msg_list = []
        for key, val in cast(ConfigParser, getattr(g.cfg, "_parser")).items("custom_message"):
            if key.startswith(m.post.message_type):
                msg_list.append(val)
        if msg_list:
            msg = random.choice(msg_list)

    try:
        msg = str(msg.format(
            user_id=m.data.user_id,
            keyword=g.cfg.search.keyword,
            start=ExtDt(g.params.get("starttime", ExtDt())).format("ymd"),
            end=ExtDt(g.params.get("onday", ExtDt())).format("ymd"),
            rpoint_diff=rpoint_diff * 100,
            rpoint_sum=m.post.rpoint_sum * 100,
        ))
    except KeyError as e:
        logging.error("[unknown keywords] %s: %s", e, msg)
        msg = msg.replace("{user_id}", m.data.user_id)

    m.post.message = msg


def header(game_info: GameInfoDict, m: MessageParserProtocol, add_text="", indent=1):
    """見出し生成

    Args:
        game_info (GameInfoDict): 集計範囲のゲーム情報
        m (MessageParserProtocol): メッセージデータ
        add_text (str, optional): 追加表示するテキスト. Defaults to "".
        indent (int, optional): 先頭のタブ数. Defaults to 1.

    Returns:
        str: 生成した見出し
    """

    msg = ""

    # 集計範囲
    if g.params.get("search_word"):  # コメント検索の場合はコメントで表示
        game_range1 = f"最初のゲーム：{game_info["first_comment"]}\n"
        game_range1 += f"最後のゲーム：{game_info["last_comment"]}\n"
    else:
        game_range1 = f"最初のゲーム：{game_info["first_game"].format("ymdhms")}\n"
        game_range1 += f"最後のゲーム：{game_info["last_game"].format("ymdhms")}\n"
    game_range2 = f"集計範囲：{compose.text_item.aggregation_range(game_info)}\n"

    # ゲーム数
    if game_info["game_count"] == 0:
        m.post.message_type = "no_hits"
        msg += f"{random_reply(m)}"
    else:
        match g.params.get("command"):
            case "results":
                if g.params.get("target_count"):  # 直近指定がない場合は検索範囲を付ける
                    msg += game_range1
                    msg += f"総ゲーム数：{game_info["game_count"]} 回{add_text}\n"
                else:
                    msg += str(compose.text_item.search_range()) + "\n"
                    msg += game_range1
                    msg += f"ゲーム数：{game_info["game_count"]} 回{add_text}\n"
            case "ranking" | "report":
                msg += game_range2
                msg += f"集計ゲーム数：{game_info["game_count"]}\n"
            case _:
                msg += game_range2
                msg += f"総ゲーム数：{game_info["game_count"]} 回\n"

        if (remarks_text := compose.text_item.remarks(True)):
            msg += f"{remarks_text}\n"
        if (word_text := compose.text_item.search_word(True)):
            msg += f"{word_text}\n"

    return textwrap.indent(msg, "\t" * indent)
