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

    db = p.add_argument_group("DATABASE関連オプション")
    db.add_argument(
        "--init",
        action = "store_true",
        help = "DB初期化",
    )

    db.add_argument(
        "--std",
        action = "store_true",
        help = "結果を標準出力に出す",
    )

    db.add_argument(
        "-i", "--csvimport",
        metavar = "import.csv",
        help = "CSVファイルから成績をDBにインポート",
    )

    db.add_argument(
        "-e", "--export",
        action = "store_true",
        help = "CSVファイルに成績をエクスポート",
    )

    return(p.parse_args())


### デバッグ用ログレベル追加 ###
logging.trace = partial(logging.log, 19)
logging.addLevelName(19, "TRACE")

### コマンドラインオプション解析 ###
args = parser()
if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level = 19)
    else:
        print("DEBUG MODE")
        logging.basicConfig(level = logging.INFO)
else:
    logging.basicConfig(level = logging.WARNING)


### 設定ファイル読み込み ###
try:
    config = configparser.ConfigParser()
    config.read(args.config, encoding="utf-8")
    logging.info(f"configload: {args.config} -> {config.sections()}")
except:
    sys.exit()

### 固定値 ###
wind = ("東家", "南家", "西家", "北家")
guest_mark = "※"
reaction_OK = "ok"
reaction_NG = "ng"

### slack api ###
try:
    app = App(token = os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit(e)

app_var = {
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
}
