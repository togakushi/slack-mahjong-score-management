"""
integrations/slack/adapter.py
"""

import logging
from typing import TYPE_CHECKING

from integrations.base.interface import AdapterInterface
from integrations.slack.api import AdapterAPI
from integrations.slack.config import SvcConfig
from integrations.slack.functions import SvcFunctions
from integrations.slack.parser import MessageParser

if TYPE_CHECKING:
    from configparser import ConfigParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, SvcFunctions, MessageParser]):
    """slack interface"""

    interface_type = "slack"

    def __init__(self, parser: "ConfigParser"):
        self.conf = SvcConfig(main_conf=parser)
        self.api = AdapterAPI()
        self.functions = SvcFunctions(api=self.api, conf=self.conf)
        self.parser = MessageParser

        logging.debug(self.conf)
