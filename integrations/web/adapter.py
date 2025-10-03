"""
integrations/web/adapter.py
"""

from typing import TYPE_CHECKING

from integrations.base.interface import AdapterInterface
from integrations.web.api import AdapterAPI
from integrations.web.config import SvcConfig
from integrations.web.functions import WebFunctions
from integrations.web.parser import MessageParser

if TYPE_CHECKING:
    from configparser import ConfigParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, WebFunctions, MessageParser]):
    """web interface"""

    interface_type = "web"

    def __init__(self, parser: "ConfigParser"):
        self.conf = SvcConfig(config_file=parser)
        self.api = AdapterAPI()
        self.functions = WebFunctions()
        self.parser = MessageParser
