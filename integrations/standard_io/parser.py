"""
integrations/standard_io/parser.py
"""

from typing import cast

from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""
    def __init__(self, reaction_ok: str, reaction_ng: str):
        MessageParserDataMixin.__init__(self, reaction_ok, reaction_ng)
        self._command_flg: bool = False

    def parser(self, body: dict):
        self.data.status = "message_append"
        self.data.channel_id = "dummy"

        if body.get("event"):
            body = cast(dict, body["event"])

        if body.get("text"):
            self.data.text = str(body.get("text", ""))
        else:
            self.data.text = ""

        if body.get("channel_name") == "directmessage":  # スラッシュコマンド扱い
            self._command_flg = True
            self.data.channel_type = "im"
            self.data.status = "message_append"
            self.data.channel_id = body.get("channel_id", "")

    @property
    def is_command(self):
        return self._command_flg

    @property
    def check_updatable(self) -> bool:
        return True
