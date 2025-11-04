"""
integrations/discord/config.py
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from integrations.base.interface import IntegrationsConfig
from integrations.discord.events import comparison

if TYPE_CHECKING:
    from discord import ClientUser


@dataclass
class SvcConfig(IntegrationsConfig):
    """discord用個別設定値"""

    slash_command: str = field(default="mahjong")
    """スラッシュコマンド名"""

    # 突合
    comparison_word: str = field(default="成績チェック")
    """データ突合コマンド呼び出しキーワード"""
    comparison_alias: list = field(default_factory=list)
    """データ突合スラッシュコマンド別名(カンマ区切りで設定)"""
    search_after: int = field(default=7)
    """データ突合時対象にする日数"""

    # 制限
    ignore_userid: list = field(default_factory=list)
    """投稿を無視するユーザのリスト(カンマ区切りで設定)"""
    channel_limitations: list = field(default_factory=list)
    """SQLが実行できるチャンネルリスト(カンマ区切りで設定)

    未定義はすべてのチャンネルでSQLが実行できる
    """

    bot_name: Optional["ClientUser"] = field(default=None)
    """ボットの名前"""

    def __post_init__(self):
        self.read_file("discord")

        # 先頭にスラッシュが付いている場合は除去
        if self.slash_command.startswith("/"):
            self.slash_command = self.slash_command[1:]

        # スラッシュコマンド登録
        self._command_dispatcher.update({"check": comparison.main})
        for alias in self.comparison_alias:
            self._command_dispatcher.update({alias: comparison.main})

        # 個別コマンド登録
        self._keyword_dispatcher.update({
            self.comparison_word: comparison.main,
        })
