"""
tests/database/test_result_update.py
"""

import sys
from contextlib import closing

import pytest

import libs.global_value as g
from cls.score import GameResult
from cls.timekit import ExtendedDatetime as ExtDt
from cls.timekit import Format
from integrations import factory
from libs import configuration
from libs.data import modify
from libs.utils import dbutil, validator
from tests.database import param_data


@pytest.mark.parametrize(
    "draw_split, game_result, get_point, get_rank",
    list(param_data.score_insert_case_01.values()),
    ids=list(param_data.score_insert_case_01.keys()),
)
def test_score_insert(draw_split, game_result, get_point, get_rank, monkeypatch):
    """スコア登録テスト"""
    monkeypatch.setattr(sys, "argv", ["progname", "--config=tests/testdata/minimal.ini"])
    configuration.setup(init_db=False)
    g.cfg.setting.database_file = "memdb1?mode=memory&cache=shared"  # DB差し替え
    configuration.initialization.initialization_resultdb(g.cfg.setting.database_file)
    g.adapter = factory.select_adapter("standard_io", g.cfg)
    g.cfg.selected_service = "standard_io"

    m = g.adapter.parser()
    m.data.text = game_result
    m.data.event_ts = ExtDt().format(Format.TS)

    score_data = GameResult(**validator.check_score(m))
    score_data.set(rule_version="test", draw_split=draw_split)
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
