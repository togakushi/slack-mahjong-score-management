"""
libs/functions/message.py
"""

import logging
import random
import textwrap
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.functions import compose

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from libs.datamodels import GameInfo


def random_reply(m: "MessageParserProtocol", message_type: str) -> str:
    """メッセージをランダムに返す

    Args:
        m (MessageParserProtocol): メッセージデータ
        message_type (str): 応答メッセージの種類

    Returns:
        str: 応答メッセージ
    """

    parser = ConfigParser()
    parser.read(g.cfg.config_file, encoding="utf-8")

    correct_score = g.cfg.mahjong.origin_point * 4  # 配給原点
    rpoint_diff = abs(correct_score - m.status.rpoint_sum)

    default_message_type = {
        "invalid_argument": "使い方が間違っています。",
        "no_hits": "{start} ～ {end} に成績記録ワードが見つかりません。",
        "no_target": "集計対象データがありません。",
        "invalid_score": "素点合計：{rpoint_sum}\n点数差分：{rpoint_diff}",
        "restricted_channel": "<@{user_id}> この投稿はデータベースに反映されません。",
        "inside_thread": "<@{user_id}> スレッド内から成績登録はできません。",
        "same_player": "同名のプレイヤーがいます。",
        "not_implemented": "未実装",
        "access_denied": "アクセスが拒否されました。",
        "rule_mismatch": "集計モード(四人打/三人打)の指定と集計対象ルールに矛盾があります。",
    }

    msg = default_message_type.get(message_type, "invalid_argument")

    if g.cfg.main_parser.has_section(m.status.source):
        if channel_config := g.cfg.main_parser[m.status.source].get("channel_config"):
            parser.read(Path(channel_config), encoding="utf-8")

    if parser.has_section("custom_message"):
        msg_list = []
        for key, val in parser.items("custom_message"):
            if key.startswith(message_type):
                msg_list.append(val)
        if msg_list:
            msg = random.choice(msg_list)

    try:
        msg = str(
            msg.format(
                user_id=m.data.user_id,
                keyword=g.cfg.setting.keyword,
                start=ExtDt(g.params.get("starttime", ExtDt())).format("ymd"),
                end=ExtDt(g.params.get("onday", ExtDt())).format("ymd"),
                rpoint_diff=rpoint_diff * 100,
                rpoint_sum=m.status.rpoint_sum * 100,
            )
        )
    except KeyError as e:
        logging.error("[unknown keywords] %s: %s", e, msg)
        msg = msg.replace("{user_id}", m.data.user_id)

    return msg


def header(game_info: "GameInfo", m: "MessageParserProtocol", add_text="", indent=1):
    """見出し生成

    Args:
        game_info (GameInfo): 集計範囲のゲーム情報
        m (MessageParserProtocol): メッセージデータ
        add_text (str, optional): 追加表示するテキスト. Defaults to "".
        indent (int, optional): 先頭のタブ数. Defaults to 1.

    Returns:
        str: 生成した見出し
    """

    msg = ""
    assert isinstance(game_info.first_game, ExtDt)
    assert isinstance(game_info.last_game, ExtDt)

    # 集計範囲
    if g.params.get("search_word"):  # コメント検索の場合はコメントで表示
        game_range1 = f"最初のゲーム：{game_info.first_comment}\n"
        game_range1 += f"最後のゲーム：{game_info.last_comment}\n"
    else:
        game_range1 = f"最初のゲーム：{game_info.first_game.format('ymdhms')}\n"
        game_range1 += f"最後のゲーム：{game_info.last_game.format('ymdhms')}\n"
    game_range2 = f"集計範囲：{compose.text_item.aggregation_range(game_info)}\n"

    # ゲーム数
    if game_info.count == 0:
        msg += f"{random_reply(m, 'no_hits')}"
    else:
        match m.status.command_type:
            case "results":
                if g.params.get("target_count"):  # 直近指定がない場合は検索範囲を付ける
                    msg += game_range1
                    msg += f"集計対象：{game_info.count} ゲーム {add_text}\n"
                else:
                    msg += f"検索範囲：{str(compose.text_item.search_range(time_pattern='time'))}\n"
                    msg += game_range1
                    msg += f"集計対象：{game_info.count} ゲーム {add_text}\n"
            case "ranking" | "report":
                msg += game_range2
                msg += f"集計対象：{game_info.count} ゲーム\n"
            case _:
                msg += game_range2
                msg += f"集計対象：{game_info.count} ゲーム\n"

        if remarks_text := compose.text_item.remarks(True):
            msg += f"{remarks_text}\n"
        if word_text := compose.text_item.search_word(True):
            msg += f"{word_text}\n"

    return textwrap.indent(msg, "\t" * indent)
