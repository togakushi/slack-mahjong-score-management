import argparse
import configparser
import logging
import sys
import os

from functools import partial
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        "--moderate",
        action = "store_true",
        help = "ログレベルがエラー以下のもを非表示",
    )

    p.add_argument(
        "--notime",
        action = "store_true",
        help = "ログフォーマットから日時を削除",
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
# TRACE
logging.TRACE = 19
logging.trace = partial(logging.log, logging.TRACE)
logging.addLevelName(logging.TRACE, "TRACE")
# NOTICE
logging.NOTICE = 25
logging.notice = partial(logging.log, logging.NOTICE)
logging.addLevelName(logging.NOTICE, "NOTICE")

### コマンドラインオプション解析 ###
args = parser()

if args.notime:
    fmt = "[%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"
else:
    fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level = logging.TRACE, format = fmt)
    else:
        print("DEBUG MODE")
        logging.basicConfig(level = logging.INFO, format = fmt)
else:
    if args.moderate:
        logging.basicConfig(level = logging.WARNING, format = fmt)
    else:
        logging.basicConfig(level = logging.NOTICE, format = fmt)


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
font_file = config["setting"].get("font_file", "ipaexg.ttf")
rule_version = config["mahjong"].get("rule_version", "")
database_file = config["database"].get("database_file", "mahjong.db")
channel_limitations = config["database"].get("channel_limitations", "")
commandword = { # チャンネル内呼び出しキーワード
    "results": config["results"].get("commandword", "麻雀成績"),
    "graph": config["graph"].get("commandword", "麻雀グラフ"),
    "ranking": config["ranking"].get("commandword", "麻雀ランキング"),
    "report": config["report"].get("commandword", "麻雀成績レポート"),
    "check": config["database"].get("commandword", "麻雀成績チェック"),
    "remarks_word": config["setting"].get("remarks_word", "麻雀成績メモ"),
}

app_var = { # ホームタブ用
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
}

### slack api ###
try:
    app = App(token = os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit(e)
