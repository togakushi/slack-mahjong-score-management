import argparse
import configparser
import logging
import os

from slack_bolt import App
from slack_sdk import WebClient


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
        "-c", "--config",
        required = True,
        metavar = "config.ini",
        help = "設定ファイル",
    )

    p.add_argument(
        "-m", "--member",
        required = True,
        metavar = "member.ini",
        help = "メンバー情報ファイル",
    )

    return(p.parse_args())


### コマンドラインオプション解析 ###
args = parser()
if args.debug:
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

try:
    player_list = configparser.ConfigParser()
    player_list.read(args.member, encoding="utf-8")
    logging.info(f"configload: {args.member} -> {player_list.sections()}")
except:
    sys.exit()

### slack api ###
app = App(token = os.environ["SLACK_BOT_TOKEN"])
webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
