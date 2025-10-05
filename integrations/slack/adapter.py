"""
integrations/slack/adapter.py
"""

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
        self.conf = SvcConfig(config_file=parser)
        self.api = AdapterAPI(self.conf)
        self.functions = SvcFunctions(self.conf)
        self.parser = MessageParser
