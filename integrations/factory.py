"""
integrations/factory.py
"""

from integrations.base import interface as base
from integrations import slack
from integrations import standard_out


def select_adapter(selected_service: str) -> base.APIInterface:
    """AIPインターフェース"""

    match selected_service:
        case "slack":
            return slack.adapter.SlackAPI()
        case _:
            return standard_out.adapter.StandardOut()


def select_parser(selected_service: str) -> base.MessageParserInterface:
    """メッセージパーサ"""

    match selected_service:
        case "slack":
            return slack.parser.MessageParser()
        case _:
            return standard_out.parser.MessageParser()
