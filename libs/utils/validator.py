"""
libs/utils/validator.py
"""

import re
from typing import Literal

import libs.global_value as g
from cls.parser import CommandParser
from cls.score import GameResult
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

    if ret_flg and name in g.cfg.word_list():
        ret_flg, ret_msg = False, "コマンドに使用される単語では登録できません。"

    return (ret_flg, ret_msg)


def pattern(text: str) -> GameResult:
    """成績記録用フォーマットチェック

    Args:
        text (str): slackにポストされた内容

    Returns:
        GameResult: スコアデータ
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

    # 情報取り出し
    result = GameResult()
    position: dict[str, int] = {}
    match text:
        case text if pattern1.findall(text):
            msg = pattern1.findall(text)[0]
            position = {
                "p1_name": 1, "p1_str": 2,
                "p2_name": 3, "p2_str": 4,
                "p3_name": 5, "p3_str": 6,
                "p4_name": 7, "p4_str": 8,
            }
            comment = None
        case text if pattern2.findall(text):
            msg = pattern2.findall(text)[0]
            position = {
                "p1_name": 0, "p1_str": 1,
                "p2_name": 2, "p2_str": 3,
                "p3_name": 4, "p3_str": 5,
                "p4_name": 6, "p4_str": 7,
            }
            comment = None
        case text if pattern3.findall(text):
            msg = pattern3.findall(text)[0]
            position = {
                "p1_name": 2, "p1_str": 3,
                "p2_name": 4, "p2_str": 5,
                "p3_name": 6, "p3_str": 7,
                "p4_name": 8, "p4_str": 9,
            }
            comment = str(msg[1])
        case text if pattern4.findall(text):
            msg = pattern4.findall(text)[0]
            position = {
                "p1_name": 0, "p1_str": 1,
                "p2_name": 2, "p2_str": 3,
                "p3_name": 4, "p3_str": 5,
                "p4_name": 6, "p4_str": 7,
            }
            comment = str(msg[9])
        case _:
            return result

    g.params.update(unregistered_replace=False)  # ゲスト無効
    g.params.update(individual=True)

    result.set(comment=comment)
    for k, p in position.items():
        if str(k).endswith("_name"):
            result.set(**{k: formatter.name_replace(str(msg[p]), False)})
            continue
        result.set(**{k: str(msg[p])})

    return result


def is_data_change(slack_data: GameResult, db_data: GameResult) -> bool:
    """スコアデータに更新があるかチェックする

    Args:
        slack_data (GameResult): ポストされたデータ
        db_data (GameResult): DB記録済みデータ

    Returns:
        bool: 真偽
    """

    if slack_data.to_dict() == db_data.to_dict():
        return True
    return False
