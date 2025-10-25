"""
integrations/discord/parser.py
"""

from typing import TYPE_CHECKING, cast

from discord.channel import TextChannel

import libs.global_value as g
from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.protocols import MsgData, PostData, StatusData

if TYPE_CHECKING:
    from discord import Message

    from integrations.discord.adapter import ServiceAdapter


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    data: MsgData
    post: PostData
    status: StatusData

    def __init__(self):
        MessageParserDataMixin.__init__(self)
        self.data = MsgData()
        self.post = PostData()
        self.status = StatusData()

    def parser(self, body: "Message"):
        self.discord_msg = body

        self.data.text = self.discord_msg.content.strip()
        self.data.event_ts = str(self.discord_msg.created_at.timestamp())
        self.data.thread_ts = "0"

    @property
    def is_command(self) -> bool:
        return False

    @property
    def is_bot(self) -> bool:
        return self.discord_msg.author.bot

    @property
    def check_updatable(self) -> bool:
        g.adapter = cast("ServiceAdapter", g.adapter)

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
