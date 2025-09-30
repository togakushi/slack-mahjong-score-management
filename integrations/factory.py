"""
integrations/factory.py
"""

from configparser import ConfigParser
from typing import Literal, TypeAlias, Union, cast, overload

from cls.config import AppConfig
from integrations import slack, standard_io, web

AdapterType: TypeAlias = Union[
    "slack.adapter.ServiceAdapter",
    "web.adapter.ServiceAdapter",
    "standard_io.adapter.ServiceAdapter",
]


@overload
def select_adapter(selected_service: Literal["slack"], conf: AppConfig) -> slack.adapter.ServiceAdapter:
    ...


@overload
def select_adapter(selected_service: Literal["web"], conf: AppConfig) -> web.adapter.ServiceAdapter:
    ...


@overload
def select_adapter(selected_service: Literal["standard_io"], conf: AppConfig) -> standard_io.adapter.ServiceAdapter:
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
            return slack.adapter.ServiceAdapter(parser)
        case "web":
            return web.adapter.ServiceAdapter(parser)
        case "standard_io":
            return standard_io.adapter.ServiceAdapter(parser)
        case _:
            raise ValueError(f"Unknown service: {selected_service}")
