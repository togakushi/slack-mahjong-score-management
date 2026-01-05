"""
integrations/standard_io/adapter.py
"""

import logging
from typing import TYPE_CHECKING

from integrations.base.interface import AdapterInterface
from integrations.standard_io.api import AdapterAPI
from integrations.standard_io.config import SvcConfig
from integrations.standard_io.functions import SvcFunctions
from integrations.standard_io.parser import MessageParser

if TYPE_CHECKING:
    from configparser import ConfigParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, SvcFunctions, MessageParser]):
    """standard input/output interface"""

    interface_type = "standard_io"

    def __init__(self, parser: "ConfigParser"):
        self.conf = SvcConfig(main_conf=parser)
        self.api = AdapterAPI()
        self.functions = SvcFunctions()
        self.parser = MessageParser

        logging.debug(self.conf)
