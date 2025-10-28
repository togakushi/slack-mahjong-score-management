"""
integrations/discord/parser.py
"""

from typing import TYPE_CHECKING, cast

from discord import Message, Thread
from discord.channel import TextChannel

import libs.global_value as g
from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.protocols import MsgData, PostData, StatusData

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    def __init__(self):
        MessageParserDataMixin.__init__(self)
        self.data: MsgData = MsgData()
        self.post: PostData = PostData()
        self.status: StatusData = StatusData()
        self.discord_msg: Message

    def parser(self, body: Message):
        self.discord_msg = body
        self.status.source = f"discord_{self.discord_msg.channel.id}"

        self.data.text = self.discord_msg.content.strip()
        self.data.event_ts = str(self.discord_msg.created_at.timestamp())

        self.data.thread_ts = "0"
        if self.discord_msg.reference:
            if isinstance(self.discord_msg.reference.resolved, Message):
                self.data.thread_ts = str(self.discord_msg.reference.resolved.created_at.timestamp())

    @property
    def in_thread(self) -> bool:
        """リプライメッセージか判定
        Note: slackに合わせてプロパティ名に`in_thread`を使う
        """

        if self.discord_msg.reference:
            return True
        return False

    @property
    def is_command(self) -> bool:
        return False

    @property
    def is_bot(self) -> bool:
        return self.discord_msg.author.bot

    @property
    def check_updatable(self) -> bool:
        g.adapter = cast("ServiceAdapter", g.adapter)

        # スレッド内では常に禁止
        if isinstance(self.discord_msg.channel, Thread):
            return False

        # 禁止リストが空の場合は全チャンネルで許可
        if not g.adapter.conf.channel_limitations:
            return True

        # チャンネルIDでチェック
        if self.discord_msg.channel.id in g.adapter.conf.channel_limitations:
            return True

        # チャンネル名でチェック
        if isinstance(self.discord_msg.channel, TextChannel):
            if self.discord_msg.channel.name in g.adapter.conf.channel_limitations:
                return True

        return False

    @property
    def ignore_user(self) -> bool:
        return False
