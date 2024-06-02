from lib.database import generate
from lib.database import common
from lib.database import aggregate
from lib.database import comparison
from lib.database import initialization


# 共通クエリ
sql_result_insert = """
    insert into
        result (
            ts, playtime,
            p1_name, p1_str, p1_rpoint, p1_rank, p1_point,
            p2_name, p2_str, p2_rpoint, p2_rank, p2_point,
            p3_name, p3_str, p3_rpoint, p3_rank, p3_point,
            p4_name, p4_str, p4_rpoint, p4_rank, p4_point,
            deposit,
            rule_version, comment
        ) values (
            ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?,
            ?, ?
        )
"""


sql_result_update = """
    update result set
        p1_name=?, p1_str=?, p1_rpoint=?, p1_rank=?, p1_point=?,
        p2_name=?, p2_str=?, p2_rpoint=?, p2_rank=?, p2_point=?,
        p3_name=?, p3_str=?, p3_rpoint=?, p3_rank=?, p3_point=?,
        p4_name=?, p4_str=?, p4_rpoint=?, p4_rank=?, p4_point=?,
        deposit=?
    where ts=?
"""


sql_result_delete = "delete from result where ts=?"


sql_remarks_insert = """
    insert into
        remarks (
            thread_ts, event_ts, name, matter
        ) values (
            ?, ?, ?, ?
        )
"""


sql_remarks_delete_all = "delete from remarks where thread_ts=?"


sql_remarks_delete_one = "delete from remarks where event_ts=?"
