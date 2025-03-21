from datetime import datetime
from typing import Any

from dateutil.relativedelta import relativedelta

from cls import config

# slack object
app: Any = None
webclient: Any = None

# モジュール共通クラス
cfg = config.Config()
opt: Any = None
prm: Any = None
msg: Any = None
search_word: Any = None

args: Any = None

# 固定値
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
