"""
integrations/slack/events/slash.py
"""

from integrations.protocols import MessageParserProtocol
from libs.data import lookup


def command_help(command: str) -> dict[str, str]:
    """スラッシュコマンド用ヘルプ

    Args:
        command (str): スラッシュコマンド名

    Returns:
        dict[str, str]: ヘルプメッセージ
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

    return {"ヘルプ": msg}


def member_list(m: MessageParserProtocol):
    """メンバーリスト取得"""
    m.post.message = lookup.textdata.get_members_list()
    m.post.codeblock = True
