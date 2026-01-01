"""
libs/data/lookup/internal.py
"""

from configparser import ConfigParser
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from pathlib import Path


def get_config_value(
    config_file: "Path",
    section: str,
    name: str,
    val_type: type,
    fallback: Union[bool, int, float, str, list, None] = None,
) -> Any:
    """設定値取得

    Args:
        config_file (Path): 設定ファイルパス
        section (str): セクション名
        name (str): 項目名
        val_type (type): 取り込む値の型 (bool, int, float, str, list)
        fallback (Union[bool, int, float, str, list], optional): 項目が見つからない場合に返す値. Defaults to None

    Returns:
        Any: 取得した値
            - 実際に返す型: Union[int, float, bool, str, list, None]
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
