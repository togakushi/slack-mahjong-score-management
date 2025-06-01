"""
libs/functions/events/home_tab.py
"""

import logging

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from libs.commands.home_tab import home


def main(client, event):
    """ホームタブオープン

    Args:
        client (slack_bolt.App.client): slack_boltオブジェクト
        event (dict): イベント内容
    """

    g.app_var = {
        "view": {},
        "no": 0,
        "user_id": None,
        "view_id": None,
        "screen": None,
        "operation": None,
        "sday": g.app_var.get("sday", ExtDt().format("ymd", "-")),
        "eday": g.app_var.get("eday", ExtDt().format("ymd", "-")),
    }

    g.app_var["user_id"] = event["user"]
    if "view" in event:
        g.app_var["view_id"] = event["view"]["id"]

    logging.trace(g.app_var)  # type: ignore

    home.build_main_menu()
    result = client.views_publish(
        user_id=g.app_var["user_id"],
        view=g.app_var["view"],
    )
    logging.trace(result)  # type: ignore
