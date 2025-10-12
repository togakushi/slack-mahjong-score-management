"""
libs/utils/validator.py
"""

import re
from typing import Literal

import libs.global_value as g
from cls.command import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt
from libs.utils import formatter, textutil


def check_namepattern(name: str, kind: Literal["member", "team"]) -> tuple[bool, str]:
    """登録制限チェック

    Args:
        name (str): チェックする名前
        kind (str): チェック種別
            - member
            - team

    Returns:
        tuple[bool, str]: 判定結果
        - bool: 制限チェック結果真偽
        - str: 制限理由
    """

    def _pattern_gen(check_list: list[str]) -> list[str]:
        ret: list = []
        for x in check_list:
            ret.append(x)
            ret.append(textutil.str_conv(x, "k2h"))  # ひらがな
            ret.append(textutil.str_conv(x, "h2k"))  # カタカナ

        return list(set(ret))

    check_pattern = _pattern_gen([name, formatter.honor_remove(name)])  # 入力パターン
    ret_flg: bool = True
    ret_msg: str = "OK"

    # 名前チェック
    check_list = _pattern_gen(list(g.member_list.keys()))  # メンバーチェック
    if ret_flg and any(x in check_list for x in check_pattern):
        ret_flg, ret_msg = False, f"「{name}」は存在するメンバーです。"

    check_list = _pattern_gen([x["team"] for x in g.team_list])  # チームチェック
    if ret_flg and any(x in check_list for x in check_pattern):
        ret_flg, ret_msg = False, f"「{name}」は存在するチームです。"

    if ret_flg and g.cfg.member.guest_name in check_pattern:  # ゲストチェック
        ret_flg, ret_msg = False, "使用できない名前です。"

    # 登録規定チェック
    if ret_flg and len(name) > int(getattr(g.cfg, kind).character_limit):  # 文字制限
        ret_flg, ret_msg = False, "登録可能文字数を超えています。"

    if ret_flg and re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        ret_flg, ret_msg = False, "使用できない記号が含まれています。"

    # 引数と同名になっていないかチェック
    if ret_flg and name in ExtDt.valid_keywords():
        ret_flg, ret_msg = False, "検索範囲指定に使用される単語では登録できません。"

    if ret_flg and CommandParser().is_valid_command(name):
        ret_flg, ret_msg = False, "オプションに使用される単語では登録できません。"

    if ret_flg and name in set(list(g.keyword_dispatcher) + list(g.command_dispatcher)):
        ret_flg, ret_msg = False, "コマンドに使用される単語では登録できません。"

    return (ret_flg, ret_msg)
