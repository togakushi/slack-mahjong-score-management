"""
integrations/standard_io/parser.py
"""

from typing import cast

from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""
    def __init__(self):
        MessageParserDataMixin.__init__(self)

    def parser(self, body: dict):
        self.data.channel_id = "dummy"
        if body.get("event"):
            body = cast(dict, body["event"])

        if body.get("text"):
            self.data.text = str(body.get("text", ""))
        else:
            self.data.text = ""

    @property
    def check_updatable(self) -> bool:
        return True
