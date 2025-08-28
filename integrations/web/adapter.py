"""
integrations/standard_io/message.py
"""

from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)
from integrations.protocols import MessageParserProtocol


class _ReactionsDummy(ReactionsInterface):
    def status(self, ch=str, ts=str):
        _ = (ch, ts)

    def append(self, icon, ch, ts):
        _ = (icon, ch, ts)

    def remove(self, icon, ch, ts):
        _ = (icon, ch, ts)


class _LookupDummy(LookupInterface):
    def get_channel_id(self):
        pass

    def get_dm_channel_id(self, user_id: str):
        _ = user_id


class WebResponse(APIInterface):
    """メッセージ出力クラス"""
    def __init__(self):
        self.lookup = _LookupDummy()
        self.reactions = _ReactionsDummy()

    def post(self, m: MessageParserProtocol):
        _ = m

    def get_conversations(self, m: MessageParserProtocol):
        _ = m
