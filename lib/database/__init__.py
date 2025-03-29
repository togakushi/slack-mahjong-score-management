"""データベース関連処理集約モジュール

Exports:
- aggregate
- common
- comparison
- initialization
"""

from lib.database import aggregate, common, comparison, initialization

__all__ = ["aggregate", "common", "comparison", "initialization"]


# 共通クエリ
SQL_RESULT_INSERT = """
    insert into
        result (
            ts, playtime,
            p1_name, p1_str, p1_rpoint, p1_rank, p1_point,
            p2_name, p2_str, p2_rpoint, p2_rank, p2_point,
            p3_name, p3_str, p3_rpoint, p3_rank, p3_point,
            p4_name, p4_str, p4_rpoint, p4_rank, p4_point,
            deposit, rule_version, comment
        ) values (
            :ts, :playtime,
            :p1_name, :p1_str, :p1_rpoint, :p1_rank, :p1_point,
            :p2_name, :p2_str, :p2_rpoint, :p2_rank, :p2_point,
            :p3_name, :p3_str, :p3_rpoint, :p3_rank, :p3_point,
            :p4_name, :p4_str, :p4_rpoint, :p4_rank, :p4_point,
            :deposit, :rule_version, :comment
        )
"""

SQL_RESULT_UPDATE = """
    update result set
        p1_name=:p1_name, p1_str=:p1_str, p1_rpoint=:p1_rpoint, p1_rank=:p1_rank, p1_point=:p1_point,
        p2_name=:p2_name, p2_str=:p2_str, p2_rpoint=:p2_rpoint, p2_rank=:p2_rank, p2_point=:p2_point,
        p3_name=:p3_name, p3_str=:p3_str, p3_rpoint=:p3_rpoint, p3_rank=:p3_rank, p3_point=:p3_point,
        p4_name=:p4_name, p4_str=:p4_str, p4_rpoint=:p4_rpoint, p4_rank=:p4_rank, p4_point=:p4_point,
        deposit=:deposit, comment=:comment
    where ts=:ts
"""

SQL_RESULT_DELETE = "delete from result where ts=?"

SQL_REMARKS_INSERT = """
    insert into
        remarks (
            thread_ts, event_ts, name, matter
        ) values (
            :thread_ts, :event_ts, :name, :matter
        )
"""

SQL_REMARKS_DELETE_ALL = "delete from remarks where thread_ts=?"

SQL_REMARKS_DELETE_ONE = "delete from remarks where event_ts=?"

SQL_REMARKS_DELETE_COMPAR = """
    delete from remarks
    where
        thread_ts=:thread_ts
        and event_ts=:event_ts
        and name=:name
        and matter=:matter
    """
