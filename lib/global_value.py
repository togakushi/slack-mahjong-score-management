from datetime import datetime

from dateutil.relativedelta import relativedelta

from cls import config

# モジュール共通クラス
cfg = config.Config()

# 固定値
wind = ("東家", "南家", "西家", "北家")
member_list = {}
team_list = []
bot_id = ""
undefined_word = 2

app_var = {  # ホームタブ用初期値
    "user_id": None,
    "view_id": None,
    "screen": None,
    "operation": None,
    "sday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
}
