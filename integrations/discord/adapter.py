"""
integrations/discord/adapter.py
"""

from typing import TYPE_CHECKING

from integrations.base.interface import AdapterInterface
from integrations.discord.api import AdapterAPI
from integrations.discord.config import SvcConfig
from integrations.discord.functions import SvcFunctions
from integrations.discord.parser import MessageParser

if TYPE_CHECKING:
    from configparser import ConfigParser


class ServiceAdapter(AdapterInterface[SvcConfig, AdapterAPI, SvcFunctions, MessageParser]):
    """discord interface"""

    interface_type = "discord"

    def __init__(self, parser: "ConfigParser"):
        self.conf = SvcConfig(config_file=parser)
        self.api = AdapterAPI(self.conf)
        self.functions = SvcFunctions(self.conf)
        self.parser = MessageParser
