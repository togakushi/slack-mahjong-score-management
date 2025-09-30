"""
integrations/web/adapter.py
"""

from configparser import ConfigParser

from integrations import web
from integrations.base import interface


class AdapterAPI(interface.APIInterface):
    """ダミークラス"""

    def post(self, m: interface.MessageParserProtocol):
        """abstractmethod dummy"""

        _ = m


class AdapterInterface:
    """web interface"""

    interface_type = "web"

    def __init__(self, parser: ConfigParser):
        self.conf = web.config.AppConfig(config_file=parser)
        self.api = AdapterAPI()
        self.functions = web.functions.WebFunctions()
        self.parser = web.parser.MessageParser
