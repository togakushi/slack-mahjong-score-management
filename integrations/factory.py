"""
integrations/factory.py
"""

from integrations import slack, standard_io
from integrations.base import interface as base


def select_adapter(selected_service: str) -> base.APIInterface:
    """AIPインターフェース選択"""

    match selected_service:
        case "slack":
            return slack.adapter.SlackAPI()
        case _:
            return standard_io.adapter.StandardOut()


def select_parser(selected_service: str):
    """メッセージパーサ選択"""

    match selected_service:
        case "slack":
            return slack.parser.MessageParser()
        case _:
            return standard_io.parser.MessageParser()
