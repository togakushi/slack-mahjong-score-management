"""
integrations/slack/events/slash.py
"""

from typing import TYPE_CHECKING

from libs.types import StyleOptions

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


def command_help(m: "MessageParserProtocol"):
    """スラッシュコマンド用ヘルプ

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    msg = "```使い方："
    msg += f"\n\t{m.status.command_name} help          このメッセージ"
    msg += "\n\t--- 成績管理 ---"
    msg += f"\n\t{m.status.command_name} results       成績出力"
    msg += f"\n\t{m.status.command_name} ranking       ランキング出力"
    msg += f"\n\t{m.status.command_name} graph         ポイント推移グラフを表示"
    msg += f"\n\t{m.status.command_name} report        レポート表示"
    msg += "\n\t--- データベース操作 ---"
    msg += f"\n\t{m.status.command_name} check         データ突合"
    msg += f"\n\t{m.status.command_name} download      データベースダウンロード"
    msg += "\n\t--- メンバー管理 ---"
    msg += f"\n\t{m.status.command_name} member        登録されているメンバー"
    msg += f"\n\t{m.status.command_name} add | del     メンバーの追加/削除"
    msg += "\n\t--- チーム管理 ---"
    msg += f"\n\t{m.status.command_name} team_create <チーム名>            チームの新規作成"
    msg += f"\n\t{m.status.command_name} team_del <チーム名>               チームの削除"
    msg += f"\n\t{m.status.command_name} team_add <チーム名> <メンバー名>  チームにメンバーを登録"
    msg += f"\n\t{m.status.command_name} team_remove <メンバー名>          指定したメンバーを未所属にする"
    msg += f"\n\t{m.status.command_name} team_list                         チーム名と所属メンバーを表示"
    msg += f"\n\t{m.status.command_name} team_clear                        チームデータをすべて削除"
    msg += "```"

    m.set_data(msg, StyleOptions(title="ヘルプメッセージ"))
