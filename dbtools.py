#!/usr/bin/env python3
import logging
import os
import sys

from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import global_value as g
from lib import command as c
from lib import database as d
from lib.function import configuration

if __name__ == "__main__":
    try:
        configuration.setup()
        g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
        g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
    except SlackApiError as err:
        logging.error(err)
        sys.exit()

    # --- メンバーリスト
    c.member.read_memberslist()

    # --- 突合
    count, msg, fts = d.comparison.score_comparison()
    if fts:
        d.comparison.remarks_comparison(fts)

    print(f">>> mismatch:{count['mismatch']}, missing:{count['missing']}, delete:{count['delete']}")
