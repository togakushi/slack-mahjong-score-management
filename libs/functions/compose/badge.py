"""
libs/functions/compose/badge.py
"""

import math
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from libs.data import aggregate, lookup

if TYPE_CHECKING:
    from configparser import ConfigParser


def degree(game_count: int = 0) -> str:
    """プレイしたゲーム数に対して表示される称号を返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if g.adapter.conf.badge_degree:
        if degree_list := cast("ConfigParser", getattr(g.cfg, "_parser")).get("degree", "badge", fallback=""):
            degree_badge = degree_list.split(",")
        else:
            return ""
        if counter_list := cast("ConfigParser", getattr(g.cfg, "_parser")).get("degree", "counter", fallback=""):
            degree_counter = list(map(int, counter_list.split(",")))
            for idx, val in enumerate(degree_counter):
                if game_count >= val:
                    badge = degree_badge[idx]

    return badge


def status(game_count: int = 0, win: int = 0) -> str:
    """勝率に対して付く調子バッジを返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.
        win (int, optional): 勝ち数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if g.adapter.conf.badge_status:
        if status_list := cast("ConfigParser", getattr(g.cfg, "_parser")).get("status", "badge", fallback=""):
            status_badge = status_list.split(",")
        else:
            return badge

        if status_step := cast("ConfigParser", getattr(g.cfg, "_parser")).getfloat("status", "step", fallback=""):
            if not isinstance(status_step, float):
                return badge
            if game_count == 0:
                index = 0
            else:
                winper = win / game_count * 100
                index = 3
                for i in (1, 2, 3):
                    if winper <= 50 - status_step * i:
                        index = 4 - i
                    if winper >= 50 + status_step * i:
                        index = 2 + i

            badge = status_badge[index]

    return badge


def grade(name: str, detail: bool = True) -> str:
    """段位表示

    Args:
        name (str): 対象プレイヤー名
        detail (bool, optional): 昇段ポイントの表示. Defaults to True.

    Returns:
        str: 称号
    """

    if not g.cfg.badge.grade.table_name or not g.cfg.badge.grade.table:  # テーブル未定義
        return ""

    if not g.adapter.conf.badge_grade:  # 非表示
        return ""

    # 初期値
    point: int = 0  # 昇段ポイント
    grade_level: int = 0  # レベル(段位)

    result_df = lookup.db.get_results_list(name, g.params.get("rule_version", ""))
    addition_expression = g.cfg.badge.grade.table.get("addition_expression", "0")
    for _, data in result_df.iterrows():
        rank = data["rank"]
        rpoint = data["rpoint"]
        addition_point = math.ceil(eval(addition_expression.format(rpoint=rpoint, origin_point=g.cfg.mahjong.origin_point)))
        point, grade_level = aggregate.grade_promotion_check(grade_level, point + addition_point, rank)

    next_point = g.cfg.badge.grade.table["table"][grade_level]["point"][1]
    grade_name = g.cfg.badge.grade.table["table"][grade_level]["grade"]
    point_detail = f" ({point}/{next_point})" if detail else ""

    return f"{grade_name}{point_detail}"
