"""
lib/utils/date.py
"""

from datetime import datetime
from typing import Any, Literal


def ts_conv(ts: datetime | float | str, fmt: Literal["ts", "y", "jy", "m", "jm", "d", "hm", "hms"] | str) -> str:
    """時間書式変更

    Args:
        ts (datetime | float | str): 変更する時間
        fmt (str | None, optional): フォーマット指定. Defaults to None.
        - ts: timestamp()
        - y / jy: "%Y" / "%Y年"
        - m / jm: "%Y/%m" / "%Y年%m月"
        - d: "%Y/%m/%d"
        - hm: "%Y/%m/%d %H:%M"
        - hms: "%Y/%m/%d %H:%M:%S"

    Returns:
        str: 変更後の文字列
    """

    time_obj: Any = datetime.now()

    if isinstance(ts, str):
        time_obj = datetime.fromisoformat(ts)
    elif isinstance(ts, float):
        time_obj = datetime.fromtimestamp(ts)
    elif isinstance(ts, datetime):
        time_obj = ts

    match fmt:
        case "ts":
            ret = str(time_obj.timestamp())
        case "y":
            ret = time_obj.strftime("%Y")
        case "jy":
            ret = time_obj.strftime("%Y年")
        case "jm":
            ret = time_obj.strftime("%Y年%m月")
        case "d":
            ret = time_obj.strftime("%Y/%m/%d")
        case "hm":
            ret = time_obj.strftime("%Y/%m/%d %H:%M")
        case "hms":
            ret = time_obj.strftime("%Y/%m/%d %H:%M:%S")

    return (ret)
