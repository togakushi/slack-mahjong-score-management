"""
integrations/standard_io/adapter.py
"""

from configparser import ConfigParser

from integrations.base.interface import AdapterInterface
from integrations.standard_io.api import AdapterAPI
from integrations.standard_io.config import SvcConfig
from integrations.standard_io.functions import StandardIOFunctions
from integrations.standard_io.parser import MessageParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, StandardIOFunctions, MessageParser]):
    """standard input/output interface"""

    interface_type = "standard_io"

    def __init__(self, parser: ConfigParser):
        self.conf = SvcConfig(config_file=parser)
        self.api = AdapterAPI()
        self.functions = StandardIOFunctions()
        self.parser = MessageParser
