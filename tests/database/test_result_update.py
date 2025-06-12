"""
tests/database/test_registration.py
"""

import sys
from contextlib import closing
from unittest.mock import patch

import pytest

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.data import modify
from libs.functions import configuration, score
from libs.utils import dbutil, validator
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
    g.cfg.db.database_file = "memdb1?mode=memory&cache=shared"  # DB差し替え
    g.msg.updatable = True
    g.cfg.mahjong.draw_split = draw_split

    score_data = validator.pattern(game_result)
    assert score_data

    score.get_score(score_data)
    ts = ExtDt().format("ts")
    with (patch("libs.functions.score.reactions")):
        modify.db_insert(score_data, ts)

    with closing(dbutil.get_connection()) as conn:
        cur = conn.execute(
            """
            select
                p1_point, p1_rank,
                p2_point, p2_rank,
                p3_point, p3_rank,
                p4_point, p4_rank
            from
                result
            where
                ts=?
            ;
            """, (ts,)
        )
        db_data = dict(cur.fetchone())
        assert db_data is not None

    db_point = {k: v for k, v in db_data.items() if str(k).endswith("_point")}
    db_rank = {k: v for k, v in db_data.items() if str(k).endswith("_rank")}
    print(ts, db_point, db_rank)
    assert db_point == get_point
    assert db_rank == get_rank
