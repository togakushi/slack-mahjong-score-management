"""
integrations/slack/adapter.py
"""

from configparser import ConfigParser

from integrations import slack


class AdapterInterface:
    """slack interface"""

    interface_type = "slack"

    def __init__(self, parser: ConfigParser):
        self.conf = slack.config.AppConfig(config_file=parser)
        self.api = slack.api.AdapterAPI(self.conf)
        self.functions = slack.functions.SlackFunctions(self.conf)
        self.parser = slack.parser.MessageParser
