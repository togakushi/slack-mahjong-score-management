"""
integrations/web/api.py
"""

from integrations.base.interface import APIInterface, MessageParserProtocol


class AdapterAPI(APIInterface):
    """ダミークラス"""

    def post(self, m: MessageParserProtocol):
        """abstractmethod dummy"""

        _ = m
