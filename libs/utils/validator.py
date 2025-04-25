"""
libs/utils/validator.py
"""

import re
from typing import Tuple

import libs.global_value as g
from cls.parser import CommandParser
from cls.types import SlackSearchData
from libs.utils import textutil

SlackSearchDict = dict[str, SlackSearchData]


def check_namepattern(name: str, kind: str | None = None) -> Tuple[bool, str]:
    """登録制限チェック

    Args:
        name (str): チェックする名前
        kind (str | None, optional): チェック種別. Defaults to None.

    Returns:
        Tuple[bool,str]: 判定結果
        - bool: 制限チェック結果真偽
        - str: 制限理由
    """

    # 登録済みメンバーかチェック
    check_list = list(g.member_list.keys())
    check_list += [textutil.str_conv(i, "k2h") for i in g.member_list]  # ひらがな
    check_list += [textutil.str_conv(i, "h2k") for i in g.member_list]  # カタカナ
    if name in check_list:
        return (False, f"「{name}」は存在するメンバーです。")

    # 登録済みチームかチェック
    for x in [x["team"] for x in g.team_list]:
        if name == x:
            return (False, f"「{name}」は存在するチームです。")
        if textutil.str_conv(name, "k2h") == textutil.str_conv(x, "k2h"):  # ひらがな
            return (False, f"「{name}」は存在するチームです。")
        if textutil.str_conv(name, "h2k") == textutil.str_conv(x, "h2k"):  # カタカナ
            return (False, f"「{name}」は存在するチームです。")

    # 登録規定チェック
    if kind is not None and g.cfg.config.has_section(kind):
        if len(name) > g.cfg.config[kind].getint("character_limit", 8):  # 文字制限
            return (False, "登録可能文字数を超えています。")
    if name in [g.cfg.member.guest_name, "nan"]:  # 登録NGプレイヤー名
        return (False, "使用できない名前です。")
    if re.search("[\\;:<>(),!@#*?/`\"']", name) or not name.isprintable():  # 禁則記号
        return (False, "使用できない記号が含まれています。")

    # 引数に利用できる名前かチェック
    if g.search_word.find(name):
        return (False, "検索範囲指定に使用される単語では登録できません。")

    if CommandParser().is_valid_command(name):
        return (False, "オプションに使用される単語では登録できません。")

    if name in g.cfg.word_list():
        return (False, "コマンドに使用される単語では登録できません。")

    return (True, "OK")


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

    return (msg)
