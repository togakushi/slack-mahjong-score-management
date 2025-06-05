"""
libs/functions/message.py
"""

import logging
import math
import random
import re
import textwrap
from typing import cast

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import GameInfoDict
from libs.data import aggregate, lookup


def slash_help(command):
    """スラッシュコマンド用ヘルプ

    Args:
        command (str): スラッシュコマンド名

    Returns:
        str: ヘルプメッセージ
    """

    msg = "```使い方："
    msg += f"\n\t{command} help          このメッセージ"
    msg += "\n\t--- 成績管理 ---"
    msg += f"\n\t{command} results       成績出力"
    msg += f"\n\t{command} ranking       ランキング出力"
    msg += f"\n\t{command} graph         ポイント推移グラフを表示"
    msg += f"\n\t{command} report        レポート表示"
    msg += "\n\t--- データベース操作 ---"
    msg += f"\n\t{command} check         データ突合"
    msg += f"\n\t{command} download      データベースダウンロード"
    msg += "\n\t--- メンバー管理 ---"
    msg += f"\n\t{command} member        登録されているメンバー"
    msg += f"\n\t{command} add | del     メンバーの追加/削除"
    msg += "\n\t--- チーム管理 ---"
    msg += f"\n\t{command} team_create <チーム名>            チームの新規作成"
    msg += f"\n\t{command} team_del <チーム名>               チームの削除"
    msg += f"\n\t{command} team_add <チーム名> <メンバー名>  チームにメンバーを登録"
    msg += f"\n\t{command} team_remove <メンバー名>          指定したメンバーを未所属にする"
    msg += f"\n\t{command} team_list                         チーム名と所属メンバーを表示"
    msg += f"\n\t{command} team_clear                        チームデータをすべて削除"
    msg += "```"

    return msg


def help_message():
    """チャンネル内呼び出しキーワード用ヘルプ

    Returns:
        str: ヘルプメッセージ
    """

    msg = textwrap.dedent(f"""\
        *成績記録キーワード*
        \t{g.cfg.search.keyword}

        *機能呼び出し*
        \t`呼び出しキーワード [検索範囲] [対象メンバー] [オプション]`

        \t*成績サマリ*
        \t\t呼び出しキーワード：{g.cfg.cw.results}
        \t\t検索範囲デフォルト：{g.cfg.results.get_default("aggregation_range")}
        \t*成績グラフ*
        \t\t呼び出しキーワード：{g.cfg.cw.graph}
        \t\t検索範囲デフォルト：{g.cfg.graph.get_default("aggregation_range")}
        \t*ランキング*
        \t\t呼び出しキーワード：{g.cfg.cw.ranking}
        \t\t検索範囲デフォルト：{g.cfg.ranking.get_default("aggregation_range")}
        \t\t規定打数デフォルト：全体ゲーム数 × {g.cfg.ranking.get_default("stipulated_rate")} ＋ 1
        \t\t出力制限デフォルト：上位 {g.cfg.ranking.get_default("ranked")} 名
        \t*レポート*
        \t\t呼び出しキーワード：{g.cfg.cw.report}
        \t\t検索範囲デフォルト：{g.cfg.report.get_default("aggregation_range")}
        \t*メンバー一覧*
        \t\t呼び出しキーワード：{g.cfg.cw.member}
        \t*チーム一覧*
        \t\t呼び出しキーワード：{g.cfg.cw.team}
    """)

    # 検索範囲
    msg += "\n\n*検索範囲に指定できるキーワード*\n"
    msg += textwrap.indent(ExtDt.print_range(), "\t")

    # ルール識別子
    rule = lookup.db.rule_version_range()
    if rule:
        msg += "\n\n*ルール識別子*\n"
        for key, val in rule.items():
            msg += f"\t{key}：{val['first_time']} ～ {val['last_time']}\n"

    # メモ機能
    msg += textwrap.dedent(f"""\
        *メモ機能*
        \t`登録キーワード <対象メンバー> <登録ワード>`
        \t登録キーワード：{g.cfg.cw.remarks_word}
    """)

    words = lookup.db.regulation_list(1)
    if words:
        msg += "\n\t*卓外ポイントワード(個人清算)*\n"
        for word, ex_point in rule:
            msg += "\t\t{}：{}pt\n".format(  # pylint: disable=consider-using-f-string
                word,
                str(f"{ex_point:.1f}").replace("-", "▲"),
            )

    words = [word for word, _ in lookup.db.regulation_list(2)]
    if g.cfg.undefined_word == 2:
        words += ["未登録ワードのすべてを個別にカウント"]
    if words:
        msg += f"\n\t*個別カウントワード*\n\t\t{'、'.join(words)}\n"

    words = [word for word, _ in lookup.db.regulation_list(0)]
    if g.cfg.undefined_word == 0:
        words += ["未登録ワードのすべてを役満としてカウント"]
    if words:
        msg += f"\n\t*役満カウントワード*\n\t\t{'、'.join(words)}\n"

    msg = re.sub(r"\n\n\n", "\n\n", msg, flags=re.MULTILINE)

    return msg.strip()


def reply(message=None, rpoint_sum=0):
    """メッセージをランダムに返す

    Args:
        message (str, optional): 選択するメッセージ. Defaults to None.
        rpoint_sum (int, optional): 素点合計(1/100). Defaults to 0.

    Returns:
        str: メッセージ
    """

    correct_score = g.cfg.mahjong.origin_point * 4  # 配給原点
    rpoint_diff = abs(correct_score - rpoint_sum)

    default_message = {
        "invalid_argument": "使い方が間違っています。",
        "no_hits": "{start} ～ {end} に≪{keyword}≫はありません。",
        "no_target": "集計対象データがありません。",
        "invalid_score": "素点合計：{rpoint_sum}\n点数差分：{rpoint_diff}",
        "restricted_channel": "<@{user_id}> この投稿はデータベースに反映されません。",
        "inside_thread": "<@{user_id}> スレッド内から成績登録はできません。",
    }

    msg = default_message.get(message, "")

    if g.cfg.config.has_section("custom_message"):
        key_list = []
        for i in g.cfg.config["custom_message"]:
            if i.startswith(message):
                key_list.append(i)
        if key_list:
            msg = g.cfg.config["custom_message"][random.choice(key_list)]

    try:
        msg = msg.format(
            user_id=g.msg.user_id,
            keyword=g.cfg.search.keyword,
            start=ExtDt(g.params.get("starttime", ExtDt())).format("ymd"),
            end=ExtDt(g.params.get("onday", ExtDt())).format("ymd"),
            rpoint_diff=rpoint_diff * 100,
            rpoint_sum=rpoint_sum * 100,
        )
    except KeyError as e:
        logging.error("[unknown keywords] %s: %s", e, msg)
        msg = msg.replace("{user_id}", g.msg.user_id)

    return msg


def remarks(headword=False) -> str | list:
    """引数で指定された集計方法を注記にまとめる

    Args:
        headword (bool, optional): 見出しを付ける. Defaults to False.

    Returns:
        Union[list, str]:
        - `headword` がない場合はリストで返す
        - `headword` がある場合は文字列で返す
    """

    remark: list = []

    if g.params.get("individual"):  # 個人集計時のみ表示
        if not g.params.get("unregistered_replace"):
            remark.append("ゲスト置換なし(" + g.cfg.setting.guest_mark + "：未登録プレイヤー)")
        if not g.params.get("guest_skip"):
            remark.append("2ゲスト戦の結果を含む")
    else:  # チーム集計時
        if g.params.get("friendly_fire"):
            if g.params.get("game_results") and g.params.get("verbose"):
                remark.append("チーム同卓時の結果を含む(" + g.cfg.setting.guest_mark + ")")
            else:
                remark.append("チーム同卓時の結果を含む")
    if g.params["stipulated"] >= 2:
        remark.append(f"規定打数 {g.params["stipulated"]} G以上")
    if g.params.get("rule_version") != g.cfg.mahjong.rule_version:
        remark.append(f"集計対象ルール {g.params["rule_version"]}")

    if headword:
        if remark:
            return "特記事項：" + "、".join(remark)
        return "特記事項：なし"

    return remark


def search_word(headword=False):
    """キーワード検索条件を返す

    Args:
        headword (bool, optional): 見出しを付ける. Defaults to False.

    Returns:
        str: 条件をまとめた文字列
    """

    if g.params.get("search_word"):
        ret = g.params["search_word"].replace("%", "")
        # 集約条件
        if g.params.get("group_length"):
            ret += f"（{g.params["group_length"]}文字集約）"
    else:
        ret = ""

    if headword:
        if ret:
            return f"検索ワード：{ret}"

    return ret


def header(game_info: GameInfoDict, add_text="", indent=1):
    """見出し生成

    Args:
        game_info (GameInfoDict): 集計範囲のゲーム情報
        add_text (str, optional): 追加表示するテキスト. Defaults to "".
        indent (int, optional): 先頭のタブ数. Defaults to 1.

    Returns:
        str: 生成した見出し
    """

    msg = ""

    # 集計範囲
    if g.params.get("search_word"):  # コメント検索の場合はコメントで表示
        game_range1 = f"最初のゲーム：{game_info['first_comment']}\n"
        game_range1 += f"最後のゲーム：{game_info['last_comment']}\n"
    else:
        game_range1 = f"最初のゲーム：{game_info['first_game'].format("ymdhms")}\n"
        game_range1 += f"最後のゲーム：{game_info['last_game'].format("ymdhms")}\n"
    game_range2 = item_aggregation_range(game_info)

    # ゲーム数
    if game_info["game_count"] == 0:
        msg += f"{reply(message='no_hits')}"
    else:
        match g.params.get("command"):
            case "results":
                if g.params.get("target_count"):  # 直近指定がない場合は検索範囲を付ける
                    msg += game_range1
                    msg += f"総ゲーム数：{game_info['game_count']} 回{add_text}\n"
                else:
                    msg += item_search_range()
                    msg += game_range1
                    msg += f"ゲーム数：{game_info['game_count']} 回{add_text}\n"
            case "ranking" | "report":
                msg += game_range2
                msg += f"集計ゲーム数：{game_info['game_count']}\n"
            case _:
                msg += game_range2
                msg += f"総ゲーム数：{game_info['game_count']} 回\n"

        if remarks():
            msg += "特記事項：" + "、".join(remarks()) + "\n"
        if search_word():
            msg += "検索ワード：" + search_word() + "\n"

    return textwrap.indent(msg, "\t" * indent)


def del_blank_line(text: str):
    """空行を取り除く

    Args:
        text (str): 処理するテキスト

    Returns:
        str: 処理されたテキスト
    """

    new_text = []
    for x in text.split("\n"):
        if x.strip() == "":
            continue
        if x.strip() == "\t":
            continue
        new_text.append(x)

    return "\n".join(new_text)


def item_search_range(kind=None, time_pattern=None):
    """検索範囲を返す（ヘッダ出力用）

    Args:
        kind (str, optional): 返値のタイプ. Defaults to None.
        time_pattern (str, optional): 表示させるフォーマットを選択. Defaults to None.

    Returns:
        Union[list, str]:
        - `kind` にlistが指定されている場合はリスト
        - `kind` にstrが指定されている場合は文字列
        - `kind` がNone場合は見出し付き文字列
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
        case _:
            return f"検索範囲：{starttime} ～ {endtime}\n"


def item_aggregation_range(game_info: GameInfoDict, kind=None):
    """集計範囲を返す（ヘッダ出力用）

    Args:
        game_info (GameInfoDict): 集計範囲のゲーム情報
        kind (str, optional): 表示させるフォーマットを選択. Defaults to None.

    Returns:
        Union[list, str]:
        - `kind` にlistが指定されている場合はリスト
        - `kind` にstrが指定されている場合は文字列
        - `kind` がNone場合は見出し付き文字列
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
            return f"{first} ～ {last}\n"
        case _:
            return f"集計範囲：{first} ～ {last}\n"


def item_date_range(kind: str, prefix_a: str | None = None, prefix_b: str | None = None) -> str:
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


def badge_degree(game_count: int = 0) -> str:
    """プレイしたゲーム数に対して表示される称号を返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if g.cfg.badge.degree:
        if (degree_list := g.cfg.config.get("degree", "badge", fallback="")):
            degree_badge = degree_list.split(",")
        else:
            return ""
        if (counter_list := g.cfg.config.get("degree", "counter", fallback="")):
            degree_counter = list(map(int, counter_list.split(",")))
            for idx, val in enumerate(degree_counter):
                if game_count >= val:
                    badge = degree_badge[idx]

    return badge


def badge_status(game_count: int = 0, win: int = 0) -> str:
    """勝率に対して付く調子バッジを返す

    Args:
        game_count (int, optional): ゲーム数. Defaults to 0.
        win (int, optional): 勝ち数. Defaults to 0.

    Returns:
        str: 表示する称号
    """

    badge: str = ""

    if g.cfg.badge.status:
        if (status_list := g.cfg.config.get("status", "badge", fallback="")):
            status_badge = status_list.split(",")
        else:
            return ""
        if (status_step := g.cfg.config.getfloat("status", "step", fallback=0)):
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


def badge_grade(name: str) -> str:
    """段位表示

    Args:
        name (str): 対象プレイヤー名

    Returns:
        str: 称号
    """

    if not g.cfg.badge.grade.display:
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

    return f"{g.cfg.badge.grade.table["table"][grade_level]["grade"]} ({point}/{next_point})"
