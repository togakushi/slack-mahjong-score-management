"""
libs/data/lookup/internal.py
"""

from configparser import ConfigParser
from typing import TYPE_CHECKING, Union, overload

if TYPE_CHECKING:
    from pathlib import Path


@overload
def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type[bool],
    fallback: bool,
) -> bool: ...


@overload
def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type[int],
    fallback: int,
) -> int: ...


@overload
def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type[float],
    fallback: float,
) -> float: ...


@overload
def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type[str],
    fallback: str,
) -> str: ...


@overload
def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type[list],
    fallback: list,
) -> list: ...


def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: Union[type[bool], type[int], type[float], type[str], type[list]],
    fallback: Union[bool, int, float, str, list, None] = None,
) -> Union[int, float, bool, str, list, None]:
    """設定値取得

    Args:
        config_file (Path): 設定ファイルパス
        section (str): セクション名
        name (str): 項目名
        val_type (Union[bool, int, float, str, list]): 取り込む値の型
        fallback (Union[bool, int, float, str, list], optional): 項目が見つからない場合に返す値. Defaults to None

    Returns:
        Union[int, float, bool, str, list, None]: 取得した値
    """

    value: Union[int, float, bool, str, list, None] = fallback
    parser = ConfigParser()
    parser.read(config_file, encoding="utf-8")

    if parser.has_option(section, name):
        match val_type:
            case x if x is int:
                value = parser.getint(section, name)
            case x if x is float:
                value = parser.getfloat(section, name)
            case x if x is bool:
                value = parser.getboolean(section, name)
            case x if x is str:
                value = parser.get(section, name)
            case x if x is list:
                value = [x.strip() for x in parser.get(section, name).split(",")]
            case _:
                value = parser.get(section, name)

    return value
