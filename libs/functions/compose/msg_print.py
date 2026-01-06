"""
libs/functions/compose/msg_help.py
"""

import textwrap
from typing import TYPE_CHECKING

from table2ascii import Alignment, PresetStyle, table2ascii

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import lookup
from libs.types import StyleOptions

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def help_message(m: "MessageParserProtocol"):
    """チャンネル内呼び出しキーワード用ヘルプ

    Args:
        m (MessageParserProtocol): _description_
    """

    g.params.update(
        {
            "source": g.cfg.resolve_channel_id(m.status.source),
            "separate": g.cfg.resolve_separate_flag(m.status.source),
        }
    )
    g.cfg.rule.status_update()

    m.set_data(
        "機能呼び出し",
        "使い方：<呼び出しキーワード> [検索範囲] [対象メンバー] [オプション]",
        StyleOptions(indent=1),
    )
    m.set_data(
        "成績サマリ",
        textwrap.dedent(f"""\
        呼び出しキーワード：{"、".join(g.cfg.results.commandword)}
        検索範囲デフォルト：{g.cfg.results.aggregation_range}
        """),
        StyleOptions(indent=1),
    )
    m.set_data(
        "成績グラフ",
        textwrap.dedent(f"""\
        呼び出しキーワード：{"、".join(g.cfg.graph.commandword)}
        検索範囲デフォルト：{g.cfg.graph.aggregation_range}
        """),
        StyleOptions(indent=1),
    )
    m.set_data(
        "ランキング",
        textwrap.dedent(f"""\
        呼び出しキーワード：{"、".join(g.cfg.ranking.commandword)}
        検索範囲デフォルト：{g.cfg.ranking.aggregation_range}
        規定打数デフォルト：全体ゲーム数 × {g.cfg.ranking.stipulated_rate} ＋ 1
        出力制限デフォルト：上位 {g.cfg.ranking.ranked} 名
        """),
        StyleOptions(indent=1),
    )
    m.set_data(
        "レポート",
        textwrap.dedent(f"""\
        呼び出しキーワード：{"、".join(g.cfg.report.commandword)}
        検索範囲デフォルト：{g.cfg.report.aggregation_range}
        """),
        StyleOptions(indent=1),
    )
    m.set_data(
        "メンバー一覧",
        f"呼び出しキーワード：{'、'.join(g.cfg.member.commandword)}",
        StyleOptions(indent=1),
    )
    m.set_data(
        "チーム一覧",
        f"呼び出しキーワード：{'、'.join(g.cfg.team.commandword)}",
        StyleOptions(indent=1),
    )
    m.set_data(  # 検索範囲
        "検索範囲に指定できるキーワード",
        ExtDt.print_range(),
        StyleOptions(indent=1),
    )
    m.set_data(  # メモ機能
        "メモ機能",
        textwrap.dedent(f"""\
        使い方：<登録キーワード> <対象メンバー> <登録ワード>
        登録キーワード：{g.cfg.setting.remarks_word}
        """),
        StyleOptions(indent=1),
    )

    # レギュレーション
    if words := lookup.db.regulation_list(2):
        m.set_data(
            "卓外清算ワード(個人)",
            "\n".join(
                [
                    "{}：{}pt".format(
                        word,
                        str(f"{ex_point:.1f}").replace("-", "▲"),
                    )
                    for word, ex_point in words
                ]
            ),
            StyleOptions(indent=1),
        )

    if words := lookup.db.regulation_list(3):
        m.set_data(
            "卓外清算ワード(チーム)",
            "\n".join(
                [
                    "{}：{}pt".format(
                        word,
                        str(f"{ex_point:.1f}").replace("-", "▲"),
                    )
                    for word, ex_point in words
                ]
            ),
            StyleOptions(indent=1),
        )

    words = [word for word, _ in lookup.db.regulation_list(1)]
    if g.cfg.undefined_word == 1:
        words.append("未登録ワードのすべてを個別にカウント")
    if words:
        m.set_data(
            "個別カウントワード",
            "、".join(words),
            StyleOptions(indent=1),
        )

    words = [word for word, _ in lookup.db.regulation_list(0)]
    if g.cfg.undefined_word == 0:
        words.append("未登録ワードのすべてを役満としてカウント")
    if words:
        m.set_data(
            "役満カウントワード",
            "、".join(words),
            StyleOptions(indent=1),
        )

    # ルールセット
    rule_set: list = []
    for rule_version in g.cfg.rule.rule_list:
        rule_set.append(g.cfg.rule.print(rule_version))
    m.set_data(
        "ルールセット",
        "\n \n".join(rule_set),
        StyleOptions(indent=1, keep_blank=True),
    )

    # その他
    channel_config = g.params.get("channel_config")
    m.set_data(
        "チャンネル設定情報",
        textwrap.dedent(f"""\
        チャンネル識別子：{g.params.get("source")}
        チャンネル個別設定：{channel_config.name if channel_config else "---"}
        チャンネルセパレート：{"有効" if g.params.get("separate", False) else "無効"}
        データベースファイル：{g.cfg.setting.database_file}
        """),
        StyleOptions(indent=1),
    )


def get_members_list() -> str:
    """登録済みのメンバー一覧を取得する

    Returns:
        str: メンバーリスト
    """

    name_list: list = []
    for pname in g.cfg.member.lists:
        name_list.append([pname, ", ".join(g.cfg.member.alias(pname))])

    if name_list:
        output = table2ascii(
            header=["表示名", "登録されている名前"],
            body=name_list,
            alignments=[Alignment.LEFT, Alignment.LEFT],
            style=PresetStyle.ascii_borderless,
        )
    else:
        output = "メンバーは登録されていません。"

    return output


def get_team_list() -> str:
    """チームの登録状況を取得する

    Returns:
        str: チームリスト
    """

    team_list: list = []
    for team_name in g.cfg.team.lists:
        if member := ", ".join(g.cfg.team.member(team_name)):
            team_list.append([team_name, member])
        else:
            team_list.append([team_name, "未エントリー"])

    if team_list:
        output = table2ascii(
            header=["チーム名", "所属メンバー"],
            body=team_list,
            alignments=[Alignment.LEFT, Alignment.LEFT],
            style=PresetStyle.ascii_borderless,
        )
    else:
        output = "チームは登録されていません。"

    return output
