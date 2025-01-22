#!/usr/bin/env python3
import logging
import os
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import global_value as g
from lib import command as c
from lib import database as d
from lib.function import configuration

try:
    configuration.setup()
    g.app = App(token=os.environ["SLACK_BOT_TOKEN"])
    g.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
    from lib import event as e
    e.event.import_only()
except SlackApiError as err:
    logging.error(err)
    sys.exit()


if __name__ == "__main__":
    d.initialization.initialization_resultdb()
    c.member.read_memberslist()
    g.bot_id = g.app.client.auth_test()["user_id"]

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
