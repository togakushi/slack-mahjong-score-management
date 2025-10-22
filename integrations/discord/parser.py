"""
integrations/discord/parser.py
"""

from typing import TYPE_CHECKING, cast

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
        g.adapter = cast("ServiceAdapter", g.adapter)

        self.status.message = body
        self.data.text = body.content.strip()
        self.data.status = "message_append"
        self.data.event_ts = str(body.created_at.timestamp())
        self.data.thread_ts = "0"
        self.data.channel_id = str(body.channel.id)

    @property
    def is_command(self) -> bool:
        return False

    @property
    def is_bot(self) -> bool:
        return False

    @property
    def check_updatable(self) -> bool:
        return True

    @property
    def ignore_user(self) -> bool:
        return False
