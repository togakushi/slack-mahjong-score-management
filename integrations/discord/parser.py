"""
integrations/discord/parser.py
"""

from typing import TYPE_CHECKING, cast

import libs.global_value as g
from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.protocols import MsgData, PostData, StatusData

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter
    from discord import Message


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

    def parser(self, message: "Message"):
        g.adapter = cast("ServiceAdapter", g.adapter)

        self.status.message = message
        self.data.status = "message_append"
        self.data.text = message.content.strip()

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
