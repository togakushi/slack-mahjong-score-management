"""
integrations/factory.py
"""

from configparser import ConfigParser
from typing import Literal, cast, overload

from cls.config import AppConfig
from integrations.base.interface import AdapterInterface
from integrations.slack.adapter import ServiceAdapter as slack_adapter
from integrations.standard_io.adapter import ServiceAdapter as std_adapter
from integrations.web.adapter import ServiceAdapter as web_adapter


@overload
def select_adapter(
    selected_service: Literal["slack"],
    conf: AppConfig
) -> slack_adapter:
    ...


@overload
def select_adapter(
    selected_service: Literal["web"],
    conf: AppConfig
) -> std_adapter:
    ...


@overload
def select_adapter(
    selected_service: Literal["standard_io"],
    conf: AppConfig
) -> web_adapter:
    ...


def select_adapter(selected_service: str, conf: AppConfig) -> AdapterInterface:
    """インターフェース選択

    Args:
        selected_service (str): 選択サービス
        conf (AppConfig): 設定ファイル

    Raises:
        ValueError: 未定義サービス

    Returns:
        AdapterType: アダプタインターフェース
    """

    parser = cast(ConfigParser, getattr(conf, "_parser"))

    match selected_service:
        case "slack":
            return slack_adapter(parser)
        case "web":
            return web_adapter(parser)
        case "standard_io":
            return std_adapter(parser)
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
