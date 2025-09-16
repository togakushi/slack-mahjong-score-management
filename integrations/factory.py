"""
integrations/factory.py
"""

from typing import Literal, Union, overload

import pandas as pd

from integrations import protocols, slack, standard_io, web


@overload
def select_adapter(selected_service: Literal["slack"]) -> slack.adapter.SlackAPI:
    ...


@overload
def select_adapter(selected_service: Literal["web"]) -> web.adapter.WebResponse:
    ...


@overload
def select_adapter(selected_service: Literal["standard_io"]) -> standard_io.adapter.StandardIO:
    ...


def select_adapter(selected_service: str) -> protocols.AdapterProtocol:
    """AIPインターフェース選択"""

    match selected_service:
        case "slack":
            return slack.adapter.SlackAPI()
        case "web":
            return web.adapter.WebResponse()
        case "standard_io":
            return standard_io.adapter.StandardIO()
        case _:
            raise ValueError(f"Unknown service: {selected_service}")


@overload
def select_parser(selected_service: Literal["slack"]) -> slack.parser.MessageParser:
    ...


@overload
def select_parser(selected_service: Literal["web"]) -> web.parser.MessageParser:
    ...


@overload
def select_parser(selected_service: Literal["standard_io"]) -> standard_io.parser.MessageParser:
    ...


def select_parser(selected_service: str) -> protocols.MessageParserProtocol:
    """メッセージパーサ選択"""

    match selected_service:
        case "slack":
            pd.options.plotting.backend = "matplotlib"
            return slack.parser.MessageParser()
        case "web":
            pd.options.plotting.backend = "plotly"
            return web.parser.MessageParser()
        case "standard_io":
            pd.options.plotting.backend = "matplotlib"
            return standard_io.parser.MessageParser()
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


def load_config(selected_service: str):
    """個別設定読み込み"""

    conf: Union[
        slack.config.AppConfig,
        web.config.AppConfig,
        standard_io.config.AppConfig,
    ]

    match selected_service:
        case "slack":
            conf = slack.config.AppConfig()
            return conf
        case "web":
            conf = web.config.AppConfig()
            conf.initialization()
            return conf
        case "standard_io":
            conf = standard_io.config.AppConfig()
            return conf
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
