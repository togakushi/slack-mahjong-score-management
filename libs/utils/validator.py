"""
libs/utils/validator.py
"""

import re
from typing import TYPE_CHECKING, Literal, Optional

import libs.global_value as g
from cls.command import CommandParser
from cls.timekit import ExtendedDatetime as ExtDt
from libs.utils import formatter, textutil

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


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
    check_list = _pattern_gen(g.cfg.member.all_lists)  # メンバーチェック
    if ret_flg and any(x in check_list for x in check_pattern):
        ret_flg, ret_msg = False, f"「{name}」は存在するメンバーです。"

    check_list = _pattern_gen(g.cfg.team.lists)  # チームチェック
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

    if ret_flg and name in set(list(g.keyword_dispatcher) + list(g.command_dispatcher) + g.cfg.word_list()):
        ret_flg, ret_msg = False, "コマンドに使用される単語では登録できません。"

    return (ret_flg, ret_msg)


def check_score(m: "MessageParserProtocol") -> dict:
    """スコアチェック

    Args:
        m (MessageParserProtocol): メッセージデータ

    Returns:
        dict: 結果
    """

    text = m.data.text
    ret: dict = {}

    # 記号を置換
    replace_chr = [
        ("\uff0b", "+"),  # 全角プラス符号
        ("\u2212", "-"),  # 全角マイナス符号
        ("\uff08", "("),  # 全角丸括弧
        ("\uff09", ")"),  # 全角丸括弧
        ("\u2017", "_"),  # DOUBLE LOW LINE(半角)
        ("\u200b", " "),  # ZERO WIDTH SPACE(ゼロ幅スペース)
        ("\u200e", " "),  # LEFT-TO-RIGHT MARK(左から右へのマーク)
        ("\u200f", " "),  # RIGHT-TO-LEFT MARK(右から左へのマーク)
        ("\u2061", " "),  # FUNCTION APPLICATION(関数の適用)
        ("\u2800", " "),  # BRAILLE PATTERN BLANK(点字パターンの空白)
        ("\ufeff", " "),  # ZERO WIDTH NO-BREAK SPACE(ゼロ幅改行なしスペース)
    ]
    for z, h in replace_chr:
        text = text.replace(z, h)

    text = "".join(text.split())  # 改行/空白削除

    for keyword, rule_version in g.cfg.rule.keyword_mapping.items():
        # パターンマッチング
        if mode := g.cfg.rule.to_dict(rule_version).get("mode"):
            pattern1 = re.compile(rf"^({keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * mode + r"$")
            pattern2 = re.compile(r"^" + r"([^0-9()+-]+)([0-9+-]+)" * mode + rf"({keyword})$")
            pattern3 = re.compile(rf"^({keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * mode + r"$")
            pattern4 = re.compile(r"^" + r"([^0-9()+-]+)([0-9+-]+)" * mode + rf"({keyword})\((.+?)\)$")
        else:
            raise RuntimeError

        position_map: dict[int, dict] = {
            3: {
                "position1": {"p1_name": 1, "p1_str": 2, "p2_name": 3, "p2_str": 4, "p3_name": 5, "p3_str": 6, "comment": None},
                "position2": {"p1_name": 0, "p1_str": 1, "p2_name": 2, "p2_str": 3, "p3_name": 4, "p3_str": 5, "comment": None},
                "position3": {"p1_name": 2, "p1_str": 3, "p2_name": 4, "p2_str": 5, "p3_name": 6, "p3_str": 7, "comment": 1},
                "position4": {"p1_name": 0, "p1_str": 1, "p2_name": 2, "p2_str": 3, "p3_name": 4, "p3_str": 5, "comment": 7},
            },
            4: {
                "position1": {"p1_name": 1, "p1_str": 2, "p2_name": 3, "p2_str": 4, "p3_name": 5, "p3_str": 6, "p4_name": 7, "p4_str": 8, "comment": None},
                "position2": {"p1_name": 0, "p1_str": 1, "p2_name": 2, "p2_str": 3, "p3_name": 4, "p3_str": 5, "p4_name": 6, "p4_str": 7, "comment": None},
                "position3": {"p1_name": 2, "p1_str": 3, "p2_name": 4, "p2_str": 5, "p3_name": 6, "p3_str": 7, "p4_name": 8, "p4_str": 9, "comment": 1},
                "position4": {"p1_name": 0, "p1_str": 1, "p2_name": 2, "p2_str": 3, "p3_name": 4, "p3_str": 5, "p4_name": 6, "p4_str": 7, "comment": 9},
            },
        }

        # 情報取り出し
        position: dict[str, Optional[int]]
        match text:
            case text if pattern1.findall(text):
                msg = pattern1.findall(text)[0]
                position = position_map[mode]["position1"]
            case text if pattern2.findall(text):
                msg = pattern2.findall(text)[0]
                position = position_map[mode]["position2"]
            case text if pattern3.findall(text):
                msg = pattern3.findall(text)[0]
                position = position_map[mode]["position3"]
            case text if pattern4.findall(text):
                msg = pattern4.findall(text)[0]
                position = position_map[mode]["position4"]
            case _:
                continue

        for k, p in position.items():
            if isinstance(p, int):
                ret.update({k: str(msg[p])})
            else:
                ret.update({k: p})

        ret.update(
            source=m.status.source,
            ts=m.data.event_ts,
            **g.cfg.rule.to_dict(rule_version),
        )
        break

    return ret
