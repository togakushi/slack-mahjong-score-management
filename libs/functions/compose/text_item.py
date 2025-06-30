"""
libs/functions/compose/text_item.py
"""

from typing import Literal, cast

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict


def remarks(headword=False) -> str | list:
    """引数で指定された集計方法を注記にまとめる

    Args:
        headword (bool, optional): 見出しを付ける. Defaults to False.

    Returns:
        Union[list, str]:
        - `headword` がない場合はリストで返す
        - `headword` がある場合は文字列で返す
    """

    remark_list: list = []

    if g.params.get("individual"):  # 個人集計時のみ表示
        if not g.params.get("unregistered_replace"):
            remark_list.append("ゲスト置換なし(" + g.cfg.setting.guest_mark + "：未登録プレイヤー)")
        if not g.params.get("guest_skip"):
            remark_list.append("2ゲスト戦の結果を含む")
    else:  # チーム集計時
        if g.params.get("friendly_fire"):
            if g.params.get("game_results") and g.params.get("verbose"):
                remark_list.append("チーム同卓時の結果を含む(" + g.cfg.setting.guest_mark + ")")
            else:
                remark_list.append("チーム同卓時の結果を含む")
    if g.params["stipulated"] >= 2:
        remark_list.append(f"規定打数 {g.params["stipulated"]} G以上")
    if g.params.get("rule_version") != g.cfg.mahjong.rule_version:
        remark_list.append(f"集計対象ルール {g.params["rule_version"]}")

    if headword:
        if remark_list:
            return f"特記事項：{"、".join(remark_list)}"
        return "特記事項：なし"

    return remark_list


def search_word(headword=False) -> str:
    """キーワード検索条件を返す

    Args:
        headword (bool, optional): 見出しを付ける. Defaults to False.

    Returns:
        str: 条件をまとめた文字列
    """

    if (ret := str(g.params.get("search_word", "")).replace("%", "")):
        # 集約条件
        if g.params.get("group_length"):
            ret += f"（{g.params["group_length"]}文字集約）"
    else:
        ret = ""

    if headword:
        if ret:
            return f"検索ワード：{ret}"

    return ret


def search_range(kind: Literal["str", "list"] = "str", time_pattern=None) -> list | str:
    """検索範囲を返す（ヘッダ出力用）

    Args:
        kind (str): 返値のタイプ. Defaults to str.
        time_pattern (str, optional): 表示させるフォーマットを選択. Defaults to None.

    Returns:
        Union[list, str]:
        - `kind` にlistが指定されている場合はリスト
        - `kind` にstrが指定されている場合は文字列
    """

    starttime: str
    endtime: str

    match time_pattern:
        case "day":
            starttime = ExtDt(g.params["starttime"]).format("ts")
            endtime = ExtDt(g.params["endtime"]).format("ts")
        case "time":
            starttime = ExtDt(g.params["starttime"]).format("ymdhm")
            endtime = ExtDt(g.params["endtime"]).format("ymdhm")
        case _:
            starttime = ExtDt(g.params["starttime"]).format("ymdhms")
            endtime = ExtDt(g.params["endtime"]).format("ymdhms")

    match kind:
        case "list":
            return ([starttime, endtime])
        case "str":
            return f"{starttime} ～ {endtime}\n"


def aggregation_range(game_info: GameInfoDict, kind: Literal["list", "str"] = "str") -> list | str:
    """集計範囲を返す（ヘッダ出力用）

    Args:
        game_info (GameInfoDict): 集計範囲のゲーム情報
        kind (str): 表示させるフォーマットを選択. Defaults to str.
            - list: リストで受け取る
            - str: 文字列で受け取る

    Returns:
        Union[list, str]:
        - `kind` にlistが指定されている場合はリストで返す
        - `kind` にstrが指定されている場合は文字列で返す
    """

    if g.params.get("search_word"):  # コメント検索の場合はコメントで表示
        first = game_info["first_comment"]
        last = game_info["last_comment"]
    else:
        first = game_info["first_game"].format("ymdhm")
        last = game_info["last_game"].format("ymdhm")

    match kind:
        case "list":
            return ([first, last])
        case "str":
            return f"{first} ～ {last}"


def date_range(kind: str, prefix_a: str | None = None, prefix_b: str | None = None) -> str:
    """日付範囲文字列

    Args:
        kind (str): ExtendedDatetimeのformatメソッドに渡す引数
            - *_o:  表示にondayを使用
        prefix_a (str | None, optional): 単独で返った時の接頭辞. Defaults to None.
        prefix_b (str | None, optional): 範囲で返った時の接頭辞. Defaults to None.

    Returns:
        str: 生成文字列
    """

    ret: str
    str_st: str
    str_et: str
    st = ExtDt(g.params["starttime"])
    et = ExtDt(g.params["endtime"])
    ot = ExtDt(g.params["onday"])

    if kind.startswith("j"):
        kind = kind.replace("j", "")
        delimiter = "ja"
    else:
        delimiter = "slash"

    if kind.endswith("_o"):
        kind = kind.replace("_o", "")
        str_st = st.format(cast(ExtDt.FormatType, kind), delimiter=cast(ExtDt.DelimiterStyle, delimiter))
        str_et = ot.format(cast(ExtDt.FormatType, kind), delimiter=cast(ExtDt.DelimiterStyle, delimiter))
    else:
        str_st = st.format(cast(ExtDt.FormatType, kind), delimiter=cast(ExtDt.DelimiterStyle, delimiter))
        str_et = et.format(cast(ExtDt.FormatType, kind), delimiter=cast(ExtDt.DelimiterStyle, delimiter))

    if st.format(cast(ExtDt.FormatType, kind), delimiter="num") == ot.format(cast(ExtDt.FormatType, kind), delimiter="num"):
        if prefix_a and prefix_b:
            ret = f"{prefix_a} ({str_st})"
        else:
            ret = f"{str_st}"
    else:
        if prefix_a and prefix_b:
            ret = f"{prefix_b} ({str_st} - {str_et})"
        else:
            ret = f"{str_st} - {str_et}"

    return ret
