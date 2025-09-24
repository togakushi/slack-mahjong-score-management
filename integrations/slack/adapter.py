"""
integrations/slack/adapter.py
"""

from configparser import ConfigParser

from integrations import slack


class AdapterInterface:
    """slack interface"""

    interface_type = "slack"

    def __init__(self, parser: ConfigParser):
        self.conf = slack.config.AppConfig(_parser=parser)
        self.api = slack.api.SlackAPI(self)
        self.functions = slack.functions.SlackFunctions(self)
        self.parser = slack.parser.MessageParser
