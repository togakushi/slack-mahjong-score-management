"""
integrations/web/api.py
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from integrations.base.interface import APIInterface, MessageParserProtocol


class AdapterAPI(APIInterface):
    """ダミークラス"""

    def post(self, m: MessageParserProtocol):
        """abstractmethod dummy"""

        _ = m
