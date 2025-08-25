"""
integrations/factory.py
"""

import pandas as pd

from integrations import slack, standard_io, web
from integrations.base import interface as base


def select_adapter(selected_service: str) -> base.APIInterface:
    """AIPインターフェース選択"""

    match selected_service:
        case "slack":
            return slack.adapter.SlackAPI()
        case "standard_io":
            return standard_io.adapter.StandardIO()
        case "web":
            return web.adapter.StandardIO()
        case _:
            raise ValueError(f"Unknown service: {selected_service}")


def select_parser(selected_service: str, **kwargs):
    """メッセージパーサ選択"""

    reaction_ok = str(kwargs.get("reaction_ok", "ok"))
    reaction_ng = str(kwargs.get("reaction_ng", "ng"))

    match selected_service:
        case "slack":
            pd.options.plotting.backend = "matplotlib"
            return slack.parser.MessageParser(reaction_ok, reaction_ng)
        case "standard_io":
            pd.options.plotting.backend = "matplotlib"
            return standard_io.parser.MessageParser(reaction_ok, reaction_ng)
        case "web":
            pd.options.plotting.backend = "plotly"
            return web.parser.MessageParser(reaction_ok, reaction_ng)
        case _:
            raise ValueError("No match service name.")


def select_function(selected_service: str):
    """関数選択"""

    match selected_service:
        case "slack":
            import integrations.slack.functions as slack_func  # pylint: disable=import-outside-toplevel
            return slack_func
        case "standard_io":
            import integrations.standard_io.functions as stdio_func  # pylint: disable=import-outside-toplevel
            return stdio_func
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
