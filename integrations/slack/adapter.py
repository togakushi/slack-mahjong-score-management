"""
integrations/slack/adapter.py
"""

from configparser import ConfigParser

from integrations.base.interface import AdapterInterface
from integrations.slack.api import AdapterAPI
from integrations.slack.config import SvcConfig
from integrations.slack.functions import SlackFunctions
from integrations.slack.parser import MessageParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, SlackFunctions, MessageParser]):
    """slack interface"""

    interface_type = "slack"

    def __init__(self, parser: ConfigParser):
        self.conf = SvcConfig(config_file=parser)
        self.api = AdapterAPI(self.conf)
        self.functions = SlackFunctions(self.conf)
        self.parser = MessageParser
