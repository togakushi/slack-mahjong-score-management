import argparse
import configparser
import logging
import sys
import os

from datetime import datetime
from dateutil.relativedelta import relativedelta

from functools import partial
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def parser():
    p = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        add_help = True,
    )

    p.add_argument(
        "--debug",
        action = "store_true",
        help = "デバッグ情報表示",
    )

    p.add_argument(
        "--verbose",
        action = "store_true",
        help = "詳細デバッグ情報表示",
    )

    p.add_argument(
        "--quiet",
        action = "store_true",
        help = "ログレベルがエラー以下のもを非表示",
    )

    p.add_argument(
        "-c", "--config",
        required = True,
        metavar = "config.ini",
        help = "設定ファイル",
    )

    p.add_argument(
        "-m", "--member",
        metavar = "member.ini",
        help = "メンバー情報ファイル",
    )

    return(p.parse_args())


### ログレベル追加 ###
logging.trace = partial(logging.log, 19)
logging.addLevelName(19, "TRACE")
logging.notice = partial(logging.log, 25)
logging.addLevelName(25, "NOTICE")

### コマンドラインオプション解析 ###
args = parser()
fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level = 19, format = fmt)
    else:
        print("DEBUG MODE")
        logging.basicConfig(level = logging.INFO, format = fmt)
else:
    if args.quiet:
        logging.basicConfig(level = logging.WARNING, format = fmt)
    else:
        logging.basicConfig(level = 25, format = fmt)


### 設定ファイル読み込み ###
try:
    config = configparser.ConfigParser()
    config.read(args.config, encoding="utf-8")
    logging.notice(f"{args.config} -> {config.sections()}")
except:
    sys.exit()

### 固定値 ###
wind = ("東家", "南家", "西家", "北家")
member_list = {}
guest_name = config["member"].get("guest_name", "ゲスト")
guest_mark = config["setting"].get("guest_mark", "※")
reaction_ok = config["setting"].get("reaction_ok", "ok")
reaction_ng = config["setting"].get("reaction_ng", "ng")
rule_version = config["mahjong"].get("rule_version", "")
channel_limitations = config["database"].get("channel_limitations", "")

commandword = {
    "results": config["results"].get("commandword", "麻雀成績"),
    "graph": config["graph"].get("commandword", "麻雀グラフ"),
    "ranking": config["ranking"].get("commandword", "麻雀ランキング"),
    "record": config["record"].get("commandword", "麻雀記録"),
    "check": config["database"].get("commandword", "麻雀成績チェック"),
}

### slack api ###
try:
    app = App(token = os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit(e)

### Home App Var ###
app_var = {
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
}

### DB設定 ###
database_file = config["database"].get("database_file", "mahjong.db")
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
        )
        values (
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
