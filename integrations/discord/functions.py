"""
integrations/discord/functions.py
"""

from typing import TYPE_CHECKING

from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from integrations.base.interface import MessageParserProtocol
    from integrations.discord.config import SvcConfig


class SvcFunctions(FunctionsInterface):
    """discord専用関数"""

    def __init__(self, conf: "SvcConfig"):
        super().__init__()
        self.conf = conf
        """個別設定"""

    def post_processing(self, m: "MessageParserProtocol"):
        _ = m

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        _ = m
        return {}
