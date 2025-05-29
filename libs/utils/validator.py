"""
libs/utils/validator.py
"""

import re
from typing import Tuple

import libs.global_value as g
from cls.parser import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import SlackSearchData
from libs.utils import formatter, textutil

SlackSearchDict = dict[str, SlackSearchData]


def check_namepattern(name: str, kind: str = "") -> Tuple[bool, str]:
    """登録制限チェック

    Args:
        name (str): チェックする名前
        kind (str, optional): チェック種別. Defaults to 空欄.

    Returns:
        Tuple[bool,str]: 判定結果
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
    if ret_flg and len(name) > g.cfg.config.getint(kind, "character_limit", fallback=8):  # 文字制限
        ret_flg, ret_msg = False, "登録可能文字数を超えています。"

    if ret_flg and re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        ret_flg, ret_msg = False, "使用できない記号が含まれています。"

    # 引数と同名になっていないかチェック
    if ret_flg and name in ExtDt.valid_keywords():
        ret_flg, ret_msg = False, "検索範囲指定に使用される単語では登録できません。"

    if ret_flg and CommandParser().is_valid_command(name):
        ret_flg, ret_msg = False, "オプションに使用される単語では登録できません。"

    if ret_flg and name in g.cfg.word_list():
        ret_flg, ret_msg = False, "コマンドに使用される単語では登録できません。"

    return (ret_flg, ret_msg)


def pattern(text: str) -> list | bool:
    """成績記録用フォーマットチェック

    Args:
        text (str): slackにポストされた内容

    Returns:
        Tuple[list,bool]:
        - list: フォーマットに一致すればスペース区切りの名前と素点のペア
        - False: メッセージのパースに失敗した場合
    """

    # 記号を置換
    replace_chr = [
        (chr(0xff0b), "+"),  # 全角プラス符号
        (chr(0x2212), "-"),  # 全角マイナス符号
        (chr(0xff08), "("),  # 全角丸括弧
        (chr(0xff09), ")"),  # 全角丸括弧
        (chr(0x2017), "_"),  # DOUBLE LOW LINE(半角)
    ]
    for z, h in replace_chr:
        text = text.replace(z, h)

    text = "".join(text.split())

    # パターンマッチング
    pattern1 = re.compile(
        rf"^({g.cfg.search.keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern2 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({g.cfg.search.keyword})$"
    )
    pattern3 = re.compile(
        rf"^({g.cfg.search.keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
    )
    pattern4 = re.compile(
        r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({g.cfg.search.keyword})\((.+?)\)$"
    )

    msg: list | bool
    match text:
        case text if pattern1.findall(text):
            m = pattern1.findall(text)[0]
            msg = [m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], None]
        case text if pattern2.findall(text):
            m = pattern2.findall(text)[0]
            msg = [m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], None]
        case text if pattern3.findall(text):
            m = pattern3.findall(text)[0]
            msg = [m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[1]]
        case text if pattern4.findall(text):
            m = pattern4.findall(text)[0]
            msg = [m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[9]]
        case _:
            msg = False

    return msg
