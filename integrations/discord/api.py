"""
integrations/discord/api.py
"""

from typing import TYPE_CHECKING

from integrations.base.interface import APIInterface

if TYPE_CHECKING:
    from integrations.discord.config import SvcConfig
    from integrations.protocols import MessageParserProtocol


class AdapterAPI(APIInterface):
    """インターフェースAPI操作クラス"""

    def __init__(self, conf: "SvcConfig"):
        super().__init__()
        self.conf = conf
        """個別設定"""

    def post(self, m: "MessageParserProtocol"):
        """メッセージをポストする

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        _ = m
