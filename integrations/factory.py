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
            return standard_io.adapter.StandardIO()


def select_parser(selected_service: str, **kwargs):
    """メッセージパーサ選択"""

    reaction_ok = str(kwargs.get("reaction_ok", "ok"))
    reaction_ng = str(kwargs.get("reaction_ng", "ng"))

    match selected_service:
        case "slack":
            return slack.parser.MessageParser(reaction_ok, reaction_ng)
        case _:
            return standard_io.parser.MessageParser(reaction_ok, reaction_ng)
