"""
integrations/standard_io/parser.py
"""

from datetime import datetime
from typing import cast

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
        self._command_flg: bool = False

    def parser(self, body: dict):
        self.data.status = "message_append"
        self.data.channel_id = "dummy"
        self.data.event_ts = str(datetime.now().timestamp())
        self.data.thread_ts = self.data.event_ts

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

    def set_command_flag(self, flg: bool):
        """スラッシュコマンドフラグを上書き

        Args:
            flg (bool): フラグ
        """

        self._command_flg = flg

    @property
    def is_command(self):
        return self._command_flg

    @property
    def check_updatable(self) -> bool:
        return True

    @property
    def ignore_user(self) -> bool:
        return False
