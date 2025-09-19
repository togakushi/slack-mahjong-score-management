"""
tests/database/test_registration.py
"""

import sys
from contextlib import closing

import pytest

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from integrations import factory
from libs.data import modify
from libs.functions import configuration
from libs.utils import dbutil
from tests.database import param_data


@pytest.mark.parametrize(
    "draw_split, game_result, get_point, get_rank",
    list(param_data.score_insert_case_01.values()),
    ids=list(param_data.score_insert_case_01.keys())
)
def test_score_insert(draw_split, game_result, get_point, get_rank, monkeypatch):
    """スコア登録テスト"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup()
    g.cfg.setting.database_file = "memdb1?mode=memory&cache=shared"  # DB差し替え
    g.selected_service = "standard_io"

    m = factory.select_parser("standard_io")
    m.data.text = game_result
    m.data.event_ts = ExtDt().format("ts")

    score_data = GameResult(
        draw_split=draw_split,
        rule_version="test",
        **m.get_score(g.cfg.setting.keyword),
    )
    score_data.calc()
    assert score_data.has_valid_data()
    modify.db_insert(score_data, m)

    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        cur = conn.execute("select * from result where ts=?;", (m.data.event_ts,))
        db_data = dict(cur.fetchone())
        assert db_data is not None

    db_point = {k: v for k, v in db_data.items() if str(k).endswith("_point")}
    db_rank = {k: v for k, v in db_data.items() if str(k).endswith("_rank")}
    print(m.data.event_ts, db_point, db_rank)
    assert db_point == get_point
    assert db_rank == get_rank
