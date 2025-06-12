"""
tests/parser/test_score.py
"""

import pytest

import libs.global_value as g
from cls.config import Config
from libs.functions import configuration
from libs.utils import validator
from tests.parser import param_data


@pytest.mark.parametrize(
    "input_str, result_dict",
    list(param_data.score_pattern.values()),
    ids=list(param_data.score_pattern.keys()),
)
def test_score_report(input_str, result_dict):
    """得点入力"""
    configuration.set_loglevel()
    g.cfg = Config("tests/testdata/minimal.ini")

    ret = validator.pattern(input_str)
    print(ret)
    assert ret == result_dict
