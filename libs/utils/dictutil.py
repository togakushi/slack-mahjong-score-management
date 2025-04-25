"""
libs/utils/dictutil.py
"""

import logging
from typing import TYPE_CHECKING, Any, cast

import libs.global_value as g
from cls.parser import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup
from libs.utils import formatter

if TYPE_CHECKING:
    from cls.subcom import SubCommand


def placeholder(subcom: "SubCommand") -> dict:
    """プレースホルダに使用する辞書を生成

    Args:
        subcom (SubCommand): パラメータ

    Returns:
        dict: プレースホルダ用辞書
    """

    parser = CommandParser()
    ret_dict: dict = {}

    # 設定周りのパラメータ
    ret_dict.update(command=subcom.section)
    ret_dict.update(g.cfg.mahjong.to_dict())
    ret_dict.update(guest_name=g.cfg.member.guest_name)

    # デフォルト値の取り込み
    ret_dict.update(subcom.to_dict())

    # always_argumentの処理
    pre_param = parser.analysis_argument(subcom.always_argument)
    logging.info("%s", pre_param)
    ret_dict.update(pre_param.flags)

    # 引数の処理
    param = parser.analysis_argument(g.msg.argument)
    logging.info("%s", param)
    ret_dict.update(param.flags)  # 上書き

    # 検索範囲取得
    if param.search_range:
        search_range = param.search_range
    elif pre_param.search_range:
        search_range = pre_param.search_range
    else:
        search_range = ExtDt.range(subcom.aggregation_range)

    ret_dict.update(starttime=cast(ExtDt, min(search_range)) + {"hours": 12})
    ret_dict.update(endtime=cast(ExtDt, max(search_range)) + {"hours": 12})
    ret_dict.update(onday=max(search_range))

    # どのオプションにも該当しないキーワードはプレイヤー名 or チーム名
    player_name: str = str()
    target_player: list = []
    player_list: dict = {}
    competition_list: dict = {}
    team_list: list = lookup.internal.get_team()

    for x in param.unknown + pre_param.unknown + param.unknown:
        if x in team_list:
            target_player.append(x)
        elif ret_dict.get("individual") and ret_dict.get("unregistered_replace"):
            target_player.append(formatter.name_replace(x))
        else:
            target_player.append(x)

    if target_player:
        player_name = target_player[0]

    if ret_dict.get("all_player"):  # 全員追加
        if ret_dict.get("individual"):
            target_player += lookup.internal.get_member()
        else:
            target_player += lookup.internal.get_team()

    # リスト生成
    target_player = list(dict.fromkeys(target_player))
    for idx, name in enumerate(target_player):
        player_list[f"player_{idx}"] = name
        if name != player_name:
            competition_list[f"competition_{idx}"] = name

    ret_dict.update(player_name=player_name)
    ret_dict.update(target_player=target_player)
    ret_dict.update(player_list=player_list)
    ret_dict.update(competition_list=competition_list)

    # プレイヤーリスト/対戦相手リスト
    if ret_dict["player_list"]:
        for k, v in ret_dict["player_list"].items():
            ret_dict[k] = v
    if ret_dict["competition_list"]:
        for k, v in ret_dict["competition_list"].items():
            ret_dict[k] = v

    return (ret_dict)


def merge_dicts(dict1: Any, dict2: Any) -> dict:
    """辞書の内容をマージする

    Args:
        dict1 (Any): 1つ目の辞書
        dict2 (Any): 2つ目の辞書

    Returns:
        dict: マージされた辞書
    """

    merged: dict = {}

    for key in set(dict1) | set(dict2):
        val1: Any = dict1.get(key)
        val2: Any = dict2.get(key)

        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            merged[key] = val1 + val2
        elif isinstance(val1, str) and isinstance(val2, str):
            merged[key] = val1 + val2
        elif isinstance(val1, list) and isinstance(val2, list):
            merged[key] = sorted(list(set(val1 + val2)))
        else:
            merged[key] = val1 if val2 is None else val2

    return (merged)
