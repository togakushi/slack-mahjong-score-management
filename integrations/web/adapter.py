"""
integrations/web/adapter.py
"""

from configparser import ConfigParser

from integrations.base import interface
from integrations.web.api import AdapterAPI
from integrations.web.config import AppConfig
from integrations.web.functions import WebFunctions
from integrations.web.parser import MessageParser


class ServiceAdapter(interface.AdapterInterface[AppConfig, AdapterAPI, WebFunctions, MessageParser]):
    """web interface"""

    interface_type = "web"

    def __init__(self, parser: ConfigParser):
        self.conf = AppConfig(config_file=parser)
        self.api = AdapterAPI()
        self.functions = WebFunctions()
        self.parser = MessageParser
