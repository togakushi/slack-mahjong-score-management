"""
libs/functions/compose/msg_help.py
"""

import re
import textwrap

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup


def slash_command(command):
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


def event_message():
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
        \t\t検索範囲デフォルト：{g.cfg.results.aggregation_range}
        \t*成績グラフ*
        \t\t呼び出しキーワード：{g.cfg.cw.graph}
        \t\t検索範囲デフォルト：{g.cfg.graph.aggregation_range}
        \t*ランキング*
        \t\t呼び出しキーワード：{g.cfg.cw.ranking}
        \t\t検索範囲デフォルト：{g.cfg.ranking.aggregation_range}
        \t\t規定打数デフォルト：全体ゲーム数 × {g.cfg.ranking.stipulated_rate} ＋ 1
        \t\t出力制限デフォルト：上位 {g.cfg.ranking.ranked} 名
        \t*レポート*
        \t\t呼び出しキーワード：{g.cfg.cw.report}
        \t\t検索範囲デフォルト：{g.cfg.report.aggregation_range}
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
            msg += f"\t{key}：{val["first_time"]} ～ {val["last_time"]}\n"

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
