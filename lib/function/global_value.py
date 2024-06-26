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
        default = "config.ini",
        metavar = "config.ini",
        help = "設定ファイル",
    )

    return(p.parse_args())


### ログレベル追加 ###
# TRACE
logging.TRACE = 19  # type: ignore
logging.trace = partial(logging.log, logging.TRACE) # type: ignore
logging.addLevelName(logging.TRACE, "TRACE") # type: ignore
# NOTICE
logging.NOTICE = 25 # type: ignore
logging.notice = partial(logging.log, logging.NOTICE) # type: ignore
logging.addLevelName(logging.NOTICE, "NOTICE") # type: ignore

### コマンドラインオプション解析 ###
args = parser()

if args.notime:
    fmt = "[%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"
else:
    fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level = logging.TRACE, format = fmt) # type: ignore
    else:
        print("DEBUG MODE")
        logging.basicConfig(level = logging.INFO, format = fmt)
else:
    if args.moderate:
        logging.basicConfig(level = logging.WARNING, format = fmt)
    else:
        logging.basicConfig(level = logging.NOTICE, format = fmt) # type: ignore


### 設定ファイル読み込み ###
try:
    config = configparser.ConfigParser()
    config.read(args.config, encoding="utf-8")
    logging.notice(f"config read: {args.config} -> {config.sections()}") # type: ignore
except:
    sys.exit()

# 必須セクションチェック
for x in ("mahjong", "setting"):
    if not x in config.sections():
        sys.exit()

# オプションセクションチェック
for x in ("results", "graph", "ranking", "report", "member", "database", "help"):
    if not x in config.sections():
        config.add_section(x)

commandword = { # チャンネル内呼び出しキーワード
    "results": config["results"].get("commandword", "麻雀成績"),
    "graph": config["graph"].get("commandword", "麻雀グラフ"),
    "ranking": config["ranking"].get("commandword", "麻雀ランキング"),
    "report": config["report"].get("commandword", "麻雀成績レポート"),
}

rule_version = config["mahjong"].get("rule_version", "")
slash_command = config["setting"].get("slash_commandname", "/mahjong")
guest_mark = config["setting"].get("guest_mark", "※")
reaction_ok = config["setting"].get("reaction_ok", "ok")
reaction_ng = config["setting"].get("reaction_ng", "ng")
font_file = config["setting"].get("font_file", "ipaexg.ttf")
work_dir = config["setting"].get("work_dir", "work")
ignore_userid = [x.strip() for x in config["setting"].get("ignore_userid", "").split(",")]
commandword.update(remarks_word = config["setting"].get("remarks_word", "麻雀成績メモ"))
guest_name = config["member"].get("guest_name", "ゲスト")
database_file = config["database"].get("database_file", "mahjong.db")
channel_limitations = config["database"].get("channel_limitations", "")
commandword.update(check = config["database"].get("commandword", "麻雀成績チェック"))
commandword.update(help = config["help"].get("commandword", "ヘルプ"))

### 固定値 ###
wind = ("東家", "南家", "西家", "北家")
member_list = {}

app_var = { # ホームタブ用
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
}

logging.trace(f"commandword: {commandword}") # type: ignore
logging.info(f"slash command: {slash_command}")
logging.info(f"ignore_userid: {ignore_userid}")
logging.info(f"channel_limitations: {channel_limitations}")

# 作業用ディレクトリ作成
work_dir = os.path.join(os.path.realpath(os.path.curdir), work_dir)
if not os.path.isdir(work_dir):
    try:
        os.mkdir(work_dir)
    except:
        logging.error("Working directory creation failed !!!")
        sys.exit()

### slack api ###
try:
    app = App(token = os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit()
