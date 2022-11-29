import argparse
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

args = parser()
app = App(token = os.environ["SLACK_BOT_TOKEN"])
webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])

if args.debug:
    print("DEBUG MODE")
    logging.basicConfig(level = logging.INFO)
else:
    logging.basicConfig(level = logging.WARNING)

