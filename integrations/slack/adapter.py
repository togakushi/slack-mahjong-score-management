"""
integrations/slack/adapter.py
"""

from integrations import slack


class AdapterInterface:
    """slack interface"""

    interface_type = "slack"
    plotting_backend = "matplotlib"

    def __init__(self):
        self.api = slack.api.SlackAPI()
        self.functions = slack.functions.SlackFunctions()
        self.reactions = slack.api.ReactionsAPI()
