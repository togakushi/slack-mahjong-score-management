#!/usr/bin/env python3
import os

from slack_bolt.adapter.socket_mode import SocketModeHandler

import lib.event as e
import lib.command as c
import lib.database as d
from lib.function import global_value as g


# イベントAPI
@g.app.event("app_home_opened")
def handle_home_events(client, event):
    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    g.logging.trace(f"{g.app_var}")  # type: ignore

    result = client.views_publish(
        user_id=g.app_var["user_id"],
        view=e.build_main_menu(),
    )

    g.logging.trace(result)  # type: ignore


if __name__ == "__main__":
    d.initialization.initialization_resultdb()
    c.member.read_memberslist()

    handler = SocketModeHandler(g.app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
