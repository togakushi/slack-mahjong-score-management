"""
tests/parser/test_score.py
"""

import pytest

import libs.global_value as g
from cls.config import AppConfig
from cls.score import GameResult
from integrations.standard_io.parser import MessageParser
from libs.functions import configuration
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
    m = MessageParser()
    m.data.text = input_str
    m.data.event_ts = "1234567890.123456"

    result = GameResult(
        rule_version="test",
        **m.get_score(g.cfg.search.keyword),
    )
    result.calc()
    chk_dict: dict = {}
    if result.has_valid_data():
        chk_dict.update({k: v for k, v in result.to_dict().items() if str(k).endswith("_name")})
        chk_dict.update({k: v for k, v in result.to_dict().items() if str(k).endswith("_str")})
        chk_dict.update({"comment": result.comment})
    print("score data:", chk_dict)
    assert chk_dict == result_dict

    if result.has_valid_data():
        for x in range(3):
            result.calc(**result.to_dict())
            print("point:", x, result.to_list("point"))
            assert result.p1.point == get_point["p1_point"]
            assert result.p2.point == get_point["p2_point"]
            assert result.p3.point == get_point["p3_point"]
            assert result.p4.point == get_point["p4_point"]


@pytest.mark.parametrize(
    "rpoint_list, point_dict, rank_dict",
    list(param_data.point_calculation_pattern01.values()),
    ids=list(param_data.point_calculation_pattern01.keys()),
)
def test_point_calc_seat(rpoint_list, point_dict, rank_dict):
    """ポイント計算 (同点席順)"""
    configuration.set_loglevel()
    g.cfg = AppConfig("tests/testdata/minimal.ini")

    result = GameResult(
        ts="1234567890.123456",
        rule_version="test",
        draw_split=False,
        return_point=g.cfg.mahjong.return_point,
        origin_point=g.cfg.mahjong.origin_point,
        p1_name="東家", p1_str=rpoint_list[0],
        p2_name="南家", p2_str=rpoint_list[1],
        p3_name="西家", p3_str=rpoint_list[2],
        p4_name="北家", p4_str=rpoint_list[3],
    )
    result.calc()

    ret_point = {k: v for k, v in result.to_dict().items() if str(k).endswith("_point")}
    ret_rank = {k: v for k, v in result.to_dict().items() if str(k).endswith("_rank")}

    assert ret_point == point_dict
    assert ret_rank == rank_dict
    assert result.deposit == 0


@pytest.mark.parametrize(
    "rpoint_list, point_dict, rank_dict",
    list(param_data.point_calculation_pattern02.values()),
    ids=list(param_data.point_calculation_pattern02.keys()),
)
def test_point_calc_division(rpoint_list, point_dict, rank_dict):
    """ポイント計算 (同点山分け)"""
    configuration.set_loglevel()
    g.cfg = AppConfig("tests/testdata/minimal.ini")

    result = GameResult(
        ts="1234567890.123456",
        rule_version="test",
        draw_split=True,
        return_point=g.cfg.mahjong.return_point,
        origin_point=g.cfg.mahjong.origin_point,
        p1_name="東家", p1_str=rpoint_list[0],
        p2_name="南家", p2_str=rpoint_list[1],
        p3_name="西家", p3_str=rpoint_list[2],
        p4_name="北家", p4_str=rpoint_list[3],
    )
    result.calc()

    ret_point = {k: v for k, v in result.to_dict().items() if str(k).endswith("_point")}
    ret_rank = {k: v for k, v in result.to_dict().items() if str(k).endswith("_rank")}

    assert ret_point == point_dict
    assert ret_rank == rank_dict
    assert result.deposit == 0
