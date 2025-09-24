"""
integrations/factory.py
"""

from configparser import ConfigParser
from typing import Literal, TypeAlias, Union, cast, overload

from cls.config import AppConfig
from integrations import slack, standard_io, web

AdapterType: TypeAlias = Union[
    "slack.adapter.AdapterInterface",
    "web.adapter.AdapterInterface",
    "standard_io.adapter.AdapterInterface",
]


@overload
def select_adapter(selected_service: Literal["slack"], conf: AppConfig) -> slack.adapter.AdapterInterface:
    ...


@overload
def select_adapter(selected_service: Literal["web"], conf: AppConfig) -> web.adapter.AdapterInterface:
    ...


@overload
def select_adapter(selected_service: Literal["standard_io"], conf: AppConfig) -> standard_io.adapter.AdapterInterface:
    ...


def select_adapter(selected_service: str, conf: AppConfig) -> AdapterType:
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
            return slack.adapter.AdapterInterface(parser)
        case "web":
            return web.adapter.AdapterInterface(parser)
        case "standard_io":
            return standard_io.adapter.AdapterInterface(parser)
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
