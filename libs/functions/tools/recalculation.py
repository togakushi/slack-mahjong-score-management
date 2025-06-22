"""
libs/functions/tools/score_simulator.py
"""

import logging
from contextlib import closing

import libs.global_value as g
from cls.score import GameResult
from libs.data import modify
from libs.utils import dbutil


def main():
    """ポイント再計算"""
    modify.db_backup()
    with closing(dbutil.get_connection()) as cur:
        rows = cur.execute("select * from result where rule_version=?;", (g.cfg.mahjong.rule_version,))
        count = 0

        for row in rows:
            result = GameResult(ts=str(row["ts"]))
            result.set(**dict(row))
            result.calc()
            cur.execute(g.sql["RESULT_UPDATE"], result.to_dict())
            count += 1

        cur.commit()
    logging.notice("recalculated: %s", count)  # type: ignore
