"""
integrations/web/parser.py
"""

from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    def parser(self, body: dict):
        _ = body

    @property
    def is_command(self) -> bool:
        return False

    @property
    def check_updatable(self) -> bool:
        return True
