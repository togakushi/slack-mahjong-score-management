"""
integrations/slack/adapter.py
"""

from integrations.slack import api, functions


class AdapterInterface:
    """slack interface"""

    interface_type = "slack"
    plotting_backend = "matplotlib"

    def __init__(self):
        self.api = api.SlackAPI()
        self.functions = functions.SlackFunctions()
        self.reactions = api.ReactionsAPI()
