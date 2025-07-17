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
    from cls.config import SubCommand
    from integrations.protocols import MessageParserProtocol


def placeholder(subcom: "SubCommand", m: "MessageParserProtocol") -> dict:
    """プレースホルダに使用する辞書を生成

    Args:
        subcom (SubCommand): パラメータ
        m (MessageParserProtocol): メッセージデータ

    Returns:
        dict: プレースホルダ用辞書
    """

    parser = CommandParser()
    ret_dict: dict = {}

    # 初期化
    g.params.clear()

    # 設定周りのパラメータの取り込み
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
    param = parser.analysis_argument(m.argument)
    logging.info("%s", param)
    ret_dict.update(param.flags)  # 上書き

    # 検索範囲取得
    departure_time = ExtDt(hours=-g.cfg.setting.time_adjust)
    if (rule_version := ret_dict.get("rule_version")):  # ルールバージョンのみ先行評価
        g.params.update(rule_version=rule_version)
    if param.search_range:
        search_range = param.search_range
    elif pre_param.search_range:
        search_range = pre_param.search_range
    else:
        search_range = departure_time.range(subcom.aggregation_range)

    ret_dict.update(starttime=(departure_time.range(search_range) + {"hours": g.cfg.setting.time_adjust}).start)
    ret_dict.update(endtime=(departure_time.range(search_range) + {"hours": g.cfg.setting.time_adjust}).end)
    ret_dict.update(onday=departure_time.range(search_range).end)

    # どのオプションにも該当しないキーワードはプレイヤー名 or チーム名
    player_name: str = str()
    target_player: list = []

    check_list: list = param.unknown + pre_param.unknown
    if ret_dict.get("individual"):
        if ret_dict.get("all_player"):
            check_list.extend(lookup.internal.get_member())
        target_player = _collect_member(check_list)
    else:
        if ret_dict.get("all_player"):
            check_list.extend(lookup.internal.get_team())
        target_player = _collect_team(check_list)

    if target_player:
        player_name = target_player[0]

    # リスト生成
    player_list: dict = {}
    competition_list: dict = {}

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
        for k, v in cast(dict, ret_dict["player_list"]).items():
            ret_dict[k] = v
    if ret_dict["competition_list"]:
        for k, v in cast(dict, ret_dict["competition_list"]).items():
            ret_dict[k] = v

    return ret_dict


def _collect_member(target_list: list) -> list:
    ret_list: list = []
    save_flg = g.params.get("individual")
    g.params.update(individual=True)
    for name in list(dict.fromkeys(target_list)):
        if name in lookup.internal.get_team():
            teammates = lookup.internal.get_teammates(name)
            ret_list.extend(teammates)
            continue
        ret_list.append(formatter.name_replace(name))

    g.params.update(individual=save_flg)
    return list(dict.fromkeys(ret_list))


def _collect_team(target_list: list) -> list:
    ret_list: list = []
    for team in list(dict.fromkeys(target_list)):
        if team in lookup.internal.get_member():
            name = lookup.internal.which_team(team)
            if name:
                ret_list.append(name)
        else:
            ret_list.append(team)

    return list(dict.fromkeys(ret_list))


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

    return merged
