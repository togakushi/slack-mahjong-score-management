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

    def parser(self, _body: dict):
        g.adapter = cast("ServiceAdapter", g.adapter)
        _ = _body

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
