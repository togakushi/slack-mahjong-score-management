"""
integrations/web/parser.py
"""

from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.protocols import MsgData, PostData, StatusData


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
        self.data.status = "message_append"

    def parser(self, body: dict):
        _ = body

    @property
    def is_command(self) -> bool:
        return False

    @property
    def check_updatable(self) -> bool:
        return True

    @property
    def ignore_user(self) -> bool:
        return False
