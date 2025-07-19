"""
libs/functions/search.py
"""

from contextlib import closing

from cls.score import GameResult
from libs.utils import dbutil

DBSearchDict = dict[str, GameResult]


def for_db_score(first_ts: float | bool = False) -> DBSearchDict:
    """データベースからスコアを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        DBSearchDict: 検索した結果
    """

    if not first_ts:
        return {}

    data: DBSearchDict = {}
    with closing(dbutil.get_connection()) as conn:
        curs = conn.cursor()
        rows = curs.execute("select * from result where ts >= ?", (str(first_ts),))
        for row in rows.fetchall():
            ts = str(dict(row).get("ts", ""))
            result = GameResult()
            result.set(**dict(row))  # データ取り込みのみ（再計算しない）
            data[ts] = result

    return data


def for_db_remarks(first_ts: float | bool = False) -> list:
    """データベースからメモを検索して返す

    Args:
        first_ts (Union[float, bool], optional): 検索を開始する時刻. Defaults to False.

    Returns:
        list: 検索した結果
    """

    if not first_ts:
        return []

    # データベースからデータ取得
    data: list = []
    with closing(dbutil.get_connection()) as cur:
        # 記録済みメモ内容
        rows = cur.execute("select * from remarks where thread_ts>=?", (str(first_ts),))
        for row in rows.fetchall():
            data.append({
                "thread_ts": row["thread_ts"],
                "event_ts": row["event_ts"],
                "name": row["name"],
                "matter": row["matter"],
            })

    return data
