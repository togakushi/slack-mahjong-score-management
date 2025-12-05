"""
libs/functions/search.py
"""

from contextlib import closing
from typing import TYPE_CHECKING

import libs.global_value as g
from cls.score import GameResult
from libs.utils import dbutil

if TYPE_CHECKING:
    from libs.types import RemarkDict


def for_db_score(first_ts: float) -> list[GameResult]:
    """データベースからスコアを検索して返す

    Args:
        first_ts (float): 検索を開始する時刻

    Returns:
        list[GameResult]: 検索した結果
    """

    data: list = []
    with closing(dbutil.connection(g.cfg.setting.database_file)) as conn:
        curs = conn.cursor()
        rows = curs.execute(
            "select * from result where ts >= ? and source like ?", (str(first_ts), f"{g.adapter.interface_type}_%")
        )
        for row in rows.fetchall():
            data.append(GameResult(**dict(row)))

    return data


def for_db_remarks(first_ts: float) -> list["RemarkDict"]:
    """データベースからメモを検索して返す

    Args:
        first_ts (float): 検索を開始する時刻

    Returns:
        list[RemarkDict]: 検索した結果
    """

    data: list["RemarkDict"] = []
    with closing(dbutil.connection(g.cfg.setting.database_file)) as cur:
        # 記録済みメモ内容
        rows = cur.execute(dbutil.query("REMARKS_SELECT"), (str(first_ts), f"{g.adapter.interface_type}_%"))
        for row in rows.fetchall():
            data.append(
                {
                    "thread_ts": row["thread_ts"],
                    "event_ts": row["event_ts"],
                    "name": row["name"],
                    "matter": row["matter"],
                    "source": row["source"],
                }
            )

    return data
