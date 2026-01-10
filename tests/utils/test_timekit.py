"""
tests/utils/test_timekit.py
"""

import pytest

from cls.timekit import ExtendedDatetime as ExtDt
from tests.utils import param_data


@pytest.mark.parametrize(
    "date, keyword_list, period",
    list(param_data.date_range.values()),
    ids=list(param_data.date_range.keys()),
)
def test_keyword_range(date: str, keyword_list: list, period: list):
    """日付範囲キーワード"""

    for keyword in keyword_list:
        dt = ExtDt(date).range(keyword)

        print(f"{date}, {keyword} -> {dt.period} = {period}")
        assert dt.period == period


@pytest.mark.parametrize(
    "date, option, output",
    list(param_data.format_conv.values()),
    ids=list(param_data.format_conv.keys()),
)
def test_format_conv(date: str, option: list, output: str):
    """フォーマット変換"""

    args: dict = {}
    for x in option:
        if isinstance(x, ExtDt.FMT):
            args.update(fmt=x)
        if isinstance(x, ExtDt.DEM):
            args.update(delimiter=x)

    dt = ExtDt(date)
    assert dt.format(**args) == output
