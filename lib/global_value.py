"""
lib/global_value.py
"""

from argparse import Namespace
from datetime import datetime

from dateutil.relativedelta import relativedelta
from slack_bolt.app.app import App
from slack_sdk.web.client import WebClient

from cls.config import Config
from cls.parameter import CommandOption, Parameters
from cls.parser import MessageParser
from cls.search import SearchRange

# slack object
app: App
webclient: WebClient

# モジュール共通クラス
cfg: Config = Config()
opt: CommandOption
prm: Parameters
msg: MessageParser
search_word: SearchRange

# コマンドライン引数
args: Namespace

# 固定値
script_dir: str = ""
wind: tuple = ("東家", "南家", "西家", "北家")
member_list: dict = {}
team_list: list = []
bot_id: str = ""

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
