"""
integrations/discord/config.py
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from integrations.base.interface import IntegrationsConfig

if TYPE_CHECKING:
    from discord import ClientUser


@dataclass
class SvcConfig(IntegrationsConfig):
    """discord用個別設定値"""

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
