"""
integrations/web/adapter.py
"""

from integrations.base import interface
from integrations import web


class DummyAPIInterface(interface.APIInterface):
    """ダミークラス"""

    def post(self, m: interface.MessageParserProtocol):
        """abstractmethod dummy"""

        _ = m


class AdapterInterface:
    """web interface"""

    interface_type = "web"

    def __init__(self):
        self.api = DummyAPIInterface()
        self.functions = web.functions.WebFunctions()
