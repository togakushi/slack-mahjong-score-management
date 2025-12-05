"""
libs/functions/compose/msg_help.py
"""

import re
import textwrap

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup


def event_message() -> str:
    """チャンネル内呼び出しキーワード用ヘルプ

    Returns:
        str: ヘルプメッセージ
    """

    msg = textwrap.dedent(f"""\
        *成績記録キーワード*
        \t{g.cfg.setting.keyword}

        *機能呼び出し*
        \t`呼び出しキーワード [検索範囲] [対象メンバー] [オプション]`

        \t*成績サマリ*
        \t\t呼び出しキーワード：{"、".join(g.cfg.results.commandword)}
        \t\t検索範囲デフォルト：{g.cfg.results.aggregation_range}
        \t*成績グラフ*
        \t\t呼び出しキーワード：{"、".join(g.cfg.graph.commandword)}
        \t\t検索範囲デフォルト：{g.cfg.graph.aggregation_range}
        \t*ランキング*
        \t\t呼び出しキーワード：{"、".join(g.cfg.ranking.commandword)}
        \t\t検索範囲デフォルト：{g.cfg.ranking.aggregation_range}
        \t\t規定打数デフォルト：全体ゲーム数 × {g.cfg.ranking.stipulated_rate} ＋ 1
        \t\t出力制限デフォルト：上位 {g.cfg.ranking.ranked} 名
        \t*レポート*
        \t\t呼び出しキーワード：{"、".join(g.cfg.report.commandword)}
        \t\t検索範囲デフォルト：{g.cfg.report.aggregation_range}
        \t*メンバー一覧*
        \t\t呼び出しキーワード：{"、".join(g.cfg.member.commandword)}
        \t*チーム一覧*
        \t\t呼び出しキーワード：{"、".join(g.cfg.team.commandword)}
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
        \t登録キーワード：{g.cfg.setting.remarks_word}
    """)

    words = lookup.db.regulation_list(2)
    if words:
        msg += "\n\t*卓外清算ワード(個人)*\n"
        for word, ex_point in words:
            msg += "\t\t{}：{}pt\n".format(  # pylint: disable=consider-using-f-string
                word,
                str(f"{ex_point:.1f}").replace("-", "▲"),
            )
    words = lookup.db.regulation_list(3)
    if words:
        msg += "\n\t*卓外清算ワード(チーム)*\n"
        for word, ex_point in words:
            msg += "\t\t{}：{}pt\n".format(  # pylint: disable=consider-using-f-string
                word,
                str(f"{ex_point:.1f}").replace("-", "▲"),
            )

    words = [word for word, _ in lookup.db.regulation_list(1)]
    if g.cfg.undefined_word == 1:
        words += ["未登録ワードのすべてを個別にカウント"]
    if words:
        msg += f"\n\t*個別カウントワード*\n\t\t{'、'.join(words)}\n"

    words = [word for word, _ in lookup.db.regulation_list(0)]
    if g.cfg.undefined_word == 0:
        words += ["未登録ワードのすべてを役満としてカウント"]
    if words:
        msg += f"\n\t*役満カウントワード*\n\t\t{'、'.join(words)}\n"

    msg = re.sub(r"\n\n\n", "\n\n", msg, flags=re.MULTILINE)

    return msg.rstrip()
