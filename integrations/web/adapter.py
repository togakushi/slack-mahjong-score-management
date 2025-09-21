"""
integrations/web/adapter.py
"""

from integrations.base import interface
from integrations.web import functions


class DummyReactionsInterface(interface.ReactionsInterface):
    """ダミークラス"""

    def status(self, ch=str, ts=str, ok=str, ng=str) -> dict[str, list]:
        """abstractmethod dummy"""

        _ = (ch, ts, ok, ng)
        return {"ok": [], "ng": []}

    def append(self, icon: str, ch: str, ts: str) -> None:
        """abstractmethod dummy"""

        _ = (icon, ch, ts)

    def remove(self, icon: str, ch: str, ts: str) -> None:
        """abstractmethod dummy"""

        _ = (icon, ch, ts)


class DummyAPIInterface(interface.APIInterface):
    """ダミークラス"""

    def post(self, m: interface.MessageParserProtocol):
        """abstractmethod dummy"""

        _ = m


class AdapterInterface:
    """web interface"""

    interface_type = "web"
    plotting_backend = "plotly"

    def __init__(self):
        self.functions = functions.WebFunctions()
        self.reactions = DummyReactionsInterface()
        self.api = DummyAPIInterface()
