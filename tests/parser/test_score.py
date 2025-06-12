"""
tests/parser/test_score.py
"""

import pytest

import libs.global_value as g
from cls.config import Config
from libs.functions import configuration, score
from libs.utils import validator
from tests.parser import param_data


@pytest.mark.parametrize(
    "input_str, result_dict, get_point",
    list(param_data.score_pattern.values()),
    ids=list(param_data.score_pattern.keys()),
)
def test_score_report(input_str, result_dict, get_point):
    """得点入力"""
    configuration.set_loglevel()
    g.cfg = Config("tests/testdata/minimal.ini")

    ret = validator.pattern(input_str)
    print("score data:", ret)
    assert ret == result_dict

    if ret:
        for x in range(3):
            tmp_ret = ret.copy()
            score.get_score(tmp_ret)
            print("point:", x, [v for k, v in tmp_ret.items() if str(k).endswith("_point")])
            assert tmp_ret["p1_point"] == get_point["p1_point"]
            assert tmp_ret["p2_point"] == get_point["p2_point"]
            assert tmp_ret["p3_point"] == get_point["p3_point"]
            assert tmp_ret["p4_point"] == get_point["p4_point"]
