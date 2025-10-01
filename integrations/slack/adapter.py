"""
integrations/slack/adapter.py
"""

from configparser import ConfigParser

from integrations.base.interface import AdapterInterface
from integrations.slack.api import AdapterAPI
from integrations.slack.config import AppConfig
from integrations.slack.functions import SlackFunctions
from integrations.slack.parser import MessageParser


class ServiceAdapter(AdapterInterface[AppConfig, AdapterAPI, SlackFunctions, MessageParser]):
    """slack interface"""

    interface_type = "slack"

    def __init__(self, parser: ConfigParser):
        self.conf = AppConfig(config_file=parser)
        self.api = AdapterAPI(self.conf)
        self.functions = SlackFunctions(self.conf)
        self.parser = MessageParser
