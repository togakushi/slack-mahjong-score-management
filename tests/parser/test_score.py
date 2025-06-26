"""
tests/parser/test_score.py
"""

import pytest

import libs.global_value as g
from cls.config import AppConfig
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
    g.cfg = AppConfig("tests/testdata/minimal.ini")

    ret = validator.pattern(input_str)
    ret.calc(ts="1234567890.123456")
    chk_dict: dict = {}
    if ret.has_valid_data():
        chk_dict.update({k: v for k, v in ret.to_dict().items() if str(k).endswith("_name")})
        chk_dict.update({k: v for k, v in ret.to_dict().items() if str(k).endswith("_str")})
        chk_dict.update({"comment": ret.comment})
    print("score data:", chk_dict)
    assert chk_dict == result_dict

    if ret.has_valid_data():
        for x in range(3):
            ret.calc(**ret.to_dict())
            print("point:", x, ret.to_list("point"))
            assert ret.p1.point == get_point["p1_point"]
            assert ret.p2.point == get_point["p2_point"]
            assert ret.p3.point == get_point["p3_point"]
            assert ret.p4.point == get_point["p4_point"]


@pytest.mark.parametrize(
    "rpoint_list, point_dict, rank_dict",
    list(param_data.point_calculation_pattern01.values()),
    ids=list(param_data.point_calculation_pattern01.keys()),
)
def test_point_calc_seat(rpoint_list, point_dict, rank_dict):
    """ポイント計算 (同点席順)"""
    configuration.set_loglevel()
    g.cfg = AppConfig("tests/testdata/minimal.ini")
    g.cfg.mahjong.draw_split = False

    ret = score.calculation_point(rpoint_list)
    ret_point = {k: v for k, v in ret.items() if str(k).endswith("_point")}
    ret_rank = {k: v for k, v in ret.items() if str(k).endswith("_rank")}

    assert ret_point == point_dict
    assert ret_rank == rank_dict
    assert ret.get("deposit") == 0


@pytest.mark.parametrize(
    "rpoint_list, point_dict, rank_dict",
    list(param_data.point_calculation_pattern02.values()),
    ids=list(param_data.point_calculation_pattern02.keys()),
)
def test_point_calc_division(rpoint_list, point_dict, rank_dict):
    """ポイント計算 (同点山分け)"""
    configuration.set_loglevel()
    g.cfg = AppConfig("tests/testdata/minimal.ini")
    g.cfg.mahjong.draw_split = True

    ret = score.calculation_point(rpoint_list)
    ret_point = {k: v for k, v in ret.items() if str(k).endswith("_point")}
    ret_rank = {k: v for k, v in ret.items() if str(k).endswith("_rank")}

    assert ret_point == point_dict
    assert ret_rank == rank_dict
    assert ret.get("deposit") == 0
