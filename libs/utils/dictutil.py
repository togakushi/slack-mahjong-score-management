"""
libs/utils/dictutil.py
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import libs.global_value as g
from cls.command import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup
from libs.utils import formatter

if TYPE_CHECKING:
    from cls.config import SubCommand
    from integrations.protocols import MessageParserProtocol
    from libs.types import PlaceholderDict


def placeholder(subcom: "SubCommand", m: "MessageParserProtocol") -> "PlaceholderDict":
    """プレースホルダに使用する辞書を生成

    Args:
        subcom (SubCommand): パラメータ
        m (MessageParserProtocol): メッセージデータ

    Returns:
        PlaceholderDict: プレースホルダ用辞書
    """

    parser = CommandParser()

    # 初期化
    g.params = {}
    g.cfg.initialization()
    rule_version: str | None

    # 設定周りのパラメータの取り込み
    g.cfg.read_channel_config(m.status.source)

    # メンバー情報更新
    g.cfg.member.guest_name = lookup.db.get_guest()
    g.cfg.member.info = lookup.db.get_member_info()
    g.cfg.team.info = lookup.db.get_team_info()

    ret_dict: "PlaceholderDict" = cast(
        "PlaceholderDict",
        {
            "command": subcom.section,
            "guest_name": g.cfg.member.guest_name,
            "undefined_word": g.cfg.undefined_word,
            "source": m.status.source,
            "rule_set": {},
            **g.cfg.setting.to_dict(),
            **subcom.to_dict(),  # デフォルト値
        },
    )
    if rule_version := ret_dict.get("default_rule"):
        ret_dict.update({"rule_version": rule_version})
    else:
        ret_dict.update({"rule_version": g.cfg.mahjong.rule_version})

    # always_argumentの処理
    pre_param = parser.analysis_argument(subcom.always_argument)
    logging.debug("analysis_argument: %s", pre_param)
    ret_dict.update({**(cast(dict, pre_param.flags))})

    # 引数の処理
    param = parser.analysis_argument(m.argument)
    logging.debug("argument: %s", param)
    ret_dict.update({**(cast(dict, param.flags))})  # 上書き

    # 検索範囲取得
    departure_time = ExtDt(hours=-g.cfg.setting.time_adjust)
    if param.search_range:
        search_range = param.search_range
    elif pre_param.search_range:
        search_range = pre_param.search_range
    else:
        search_range = departure_time.range(subcom.aggregation_range)

    ret_dict.update(
        {
            "starttime": (departure_time.range(search_range) + {"hours": g.cfg.setting.time_adjust}).start,
            "endtime": (departure_time.range(search_range) + {"hours": g.cfg.setting.time_adjust}).end,
            "onday": departure_time.range(search_range).end,
        }
    )

    # どのオプションにも該当しないキーワード
    check_list: list[str] = param.unknown + pre_param.unknown

    for name in list(check_list):  # ルール識別子
        rule_version = None
        if name in g.cfg.rule.keyword_mapping:
            check_list.remove(name)
            rule_version = g.cfg.rule.keyword_mapping[name]
        elif name in g.cfg.rule.rule_list:
            check_list.remove(name)
            rule_version = name

        if rule_version:
            ret_dict.update(
                {
                    "mode": g.cfg.rule.get_mode(rule_version),
                    "rule_version": rule_version,
                    "mixed": False,
                }
            )

    player_name: str = str()
    target_player: list = []
    if ret_dict.get("individual"):  # プレイヤー名
        if ret_dict.get("all_player"):
            check_list.extend(g.cfg.member.lists)
        for name in check_list:
            if name in g.cfg.team.lists:  # チーム名がある場合は所属メンバーに展開
                target_player.extend(g.cfg.team.member(name))
            else:
                target_player.append(formatter.name_replace(name, not_replace=True))
    else:  # チーム名
        if ret_dict.get("all_player"):
            check_list.extend(g.cfg.team.lists)
        for team in check_list:
            if team in g.cfg.member.lists:
                if team_name := g.cfg.team.which(team):  # プレイヤー名がある場合は所属チームを追加
                    target_player.append(team_name)
            else:
                target_player.append(team)

    target_player = sorted(set(target_player), key=target_player.index)  # 順序を維持したまま重複排除

    if target_player:
        player_name = target_player[0]

    # リスト生成
    player_list: dict = {}
    competition_list: dict = {}

    for idx, name in enumerate(target_player):
        player_list[f"player_{idx}"] = name
        if name != player_name:
            competition_list[f"competition_{idx}"] = name

    ret_dict.update(
        {
            "player_name": player_name,
            "target_player": target_player,
            "player_list": player_list,
            "competition_list": competition_list,
        }
    )

    # 出力タイプ
    if not ret_dict.get("format"):
        ret_dict.update({"format": "default"})

    # 規定打数設定
    if ret_dict.get("mixed") and not ret_dict.get("stipulated"):  # 横断集計&規定数制限なし
        if target_player:
            ret_dict.update({"stipulated": 1})  # 個人成績
        else:
            ret_dict.update({"stipulated": 0})
    elif not ret_dict.get("stipulated"):  # 通常集計&規定数制限なし
        if subcom.section == "ranking":  # ランキングはレート計算
            ret_dict.update({"stipulated": 0})
        else:
            ret_dict.update({"stipulated": 1})

    # 集計ルール更新
    if mode := ret_dict.get("target_mode"):
        for rule_version in g.cfg.rule.get_version(mode=mode, mapping=not (ret_dict.get("mixed", False))):
            ret_dict["rule_set"].update({rule_version: g.cfg.rule.to_dict(rule_version)})
    elif ret_dict.get("rule_set", {}):
        if rule_version := ret_dict.get("rule_version"):
            ret_dict.update({"rule_set": {rule_version: g.cfg.rule.to_dict(rule_version)}})

    if departure_time.range(search_range).start == ExtDt("1900-01-01 00:00:00.000000"):
        ret_dict.update(
            {
                "starttime": lookup.db.first_record(
                    g.cfg.rule.get_version(
                        mode=ret_dict.get("mode", 4),
                        mapping=not (ret_dict.get("mixed", False)),
                    )
                )
            }
        )

    return ret_dict


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
