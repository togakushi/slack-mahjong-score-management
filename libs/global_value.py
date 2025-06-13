"""モジュール間データ共有用"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from slack_bolt.app.app import App
    from slack_sdk.web.client import WebClient

    from cls.config import Config
    from cls.parser import MessageParser
    from cls.types import TeamDataDict

args: "Namespace" = None  # type: ignore
"""コマンドライン引数"""
app: "App"
"""slack object"""
webclient: "WebClient"
"""slack object"""

# モジュール共通インスタンス
cfg: "Config"
"""Configインスタンス共有"""
msg: "MessageParser"
"""MessageParserインスタンス共有"""

# 環境パラメータ
member_list: dict = {}
"""メンバーリスト
- 別名: 表示名
"""
team_list: list["TeamDataDict"] = []
"""チームリスト
- id: チームID
- team: チーム名
- member: 所属メンバーリスト
"""
bot_id: str = ""
"""ボットID"""
params: dict = {}
"""プレースホルダ用パラメータ"""

app_var: dict = {}
"""ホームタブ用初期値"""

sql: dict = {}
"""共通クエリ"""
sql["RESULT_INSERT"] = """
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
    ;
"""

sql["RESULT_UPDATE"] = """
    update result set
        p1_name=:p1_name, p1_str=:p1_str, p1_rpoint=:p1_rpoint, p1_rank=:p1_rank, p1_point=:p1_point,
        p2_name=:p2_name, p2_str=:p2_str, p2_rpoint=:p2_rpoint, p2_rank=:p2_rank, p2_point=:p2_point,
        p3_name=:p3_name, p3_str=:p3_str, p3_rpoint=:p3_rpoint, p3_rank=:p3_rank, p3_point=:p3_point,
        p4_name=:p4_name, p4_str=:p4_str, p4_rpoint=:p4_rpoint, p4_rank=:p4_rank, p4_point=:p4_point,
        deposit=:deposit, comment=:comment
    where ts=:ts
    ;
"""

sql["RESULT_DELETE"] = "delete from result where ts=?;"

sql["REMARKS_INSERT"] = """
    insert into
        remarks (
            thread_ts, event_ts, name, matter
        ) values (
            :thread_ts, :event_ts, :name, :matter
        )
    ;
"""

sql["REMARKS_DELETE_ALL"] = "delete from remarks where thread_ts=?;"

sql["REMARKS_DELETE_ONE"] = "delete from remarks where event_ts=?;"

sql["REMARKS_DELETE_COMPAR"] = """
    delete from remarks
    where
        thread_ts=:thread_ts
        and event_ts=:event_ts
        and name=:name
        and matter=:matter
    ;
"""

sql["SELECT_ALL_RESULTS"] = """
    select
        rank, rpoint
    from
        individual_results
    where
        rule_version = :rule_version
        and name = :player_name
    ;
"""

sql["SELECT_GAME_RESULTS"] = """
    select
        p1_name, p1_str,
        p2_name, p2_str,
        p3_name, p3_str,
        p4_name, p4_str,
        comment,
        rule_version
    from
        result where ts=?;
"""
