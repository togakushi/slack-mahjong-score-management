"""
integrations/standard_io/functions.py
"""

from typing import TYPE_CHECKING

from cls.timekit import ExtendedDatetime as ExtDt
from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


class StandardIOFunctions(FunctionsInterface):
    """標準入出力専用関数"""

    def post_processing(self, m: MessageParserProtocol):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        print(ExtDt(float(m.data.event_ts)), m.status.message)

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """abstractmethod dummy"""

        _ = m
        return {}
