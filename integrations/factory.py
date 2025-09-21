"""
integrations/factory.py
"""

from configparser import ConfigParser
from typing import Literal, overload

import pandas as pd

from cls.types import AppConfigType
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


def load_config(selected_service: str, parser: ConfigParser) -> AppConfigType:
    """個別設定読み込み

    Args:
        selected_service (str): サービス選択
        parser (ConfigParser): 設定ファイル

    Raises:
        ValueError: 未定義サービス

    Returns:
        AppConfigType: 設定値
    """

    conf: AppConfigType

    match selected_service:
        case "slack":
            conf = slack.config.AppConfig()
            conf.read_file(parser=parser, selected_service="slack")

            # スラッシュコマンド登録
            conf.slash_commands.update({"help": slack.events.slash.command_help})

            conf.comparison_alias.append("check")
            conf.slash_commands.update({"check": slack.events.comparison.main})
            for alias in conf.comparison_alias:
                conf.slash_commands.update({alias: slack.events.comparison.main})

            # 個別コマンド登録
            conf.special_commands.update({
                conf.comparison_word: slack.events.comparison.main,
                f"Reminder: {conf.comparison_word}": slack.events.comparison.main,
            })

            return conf
        case "web":
            conf = web.config.AppConfig()
            conf.read_file(parser=parser, selected_service="web")
            conf.initialization()
            return conf
        case "standard_io":
            conf = standard_io.config.AppConfig()
            conf.read_file(parser=parser, selected_service="standard_io")
            return conf
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
