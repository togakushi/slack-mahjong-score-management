"""
lib/global_value.py
"""

from datetime import datetime
from typing import TYPE_CHECKING

from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    from argparse import Namespace

    from slack_bolt.app.app import App
    from slack_sdk.web.client import WebClient

    from cls.config import Config
    from cls.parser import MessageParser
    from cls.search import SearchRange

# コマンドライン引数
args: "Namespace" = None  # type: ignore

# slack object
app: "App"
webclient: "WebClient"

# モジュール共通インスタンス
cfg: "Config"
msg: "MessageParser"
search_word: "SearchRange"

# 固定値
script_dir: str = ""
member_list: dict = {}
team_list: list = []
bot_id: str = ""
params: dict = {}

app_var: dict = {  # ホームタブ用初期値
    "view": {},
    "no": 0,
    "user_id": None,
    "view_id": None,
    "screen": None,
    "operation": None,
    "sday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
}

# 共通クエリ
sql: dict = {}
sql["SQL_RESULT_UPDATE"] = """
    update result set
        p1_name=:p1_name, p1_str=:p1_str, p1_rpoint=:p1_rpoint, p1_rank=:p1_rank, p1_point=:p1_point,
        p2_name=:p2_name, p2_str=:p2_str, p2_rpoint=:p2_rpoint, p2_rank=:p2_rank, p2_point=:p2_point,
        p3_name=:p3_name, p3_str=:p3_str, p3_rpoint=:p3_rpoint, p3_rank=:p3_rank, p3_point=:p3_point,
        p4_name=:p4_name, p4_str=:p4_str, p4_rpoint=:p4_rpoint, p4_rank=:p4_rank, p4_point=:p4_point,
        deposit=:deposit, comment=:comment
    where ts=:ts
"""
