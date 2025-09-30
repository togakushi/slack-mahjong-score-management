"""
libs/functions/tools/comparison.py
"""

import logging
import os
from typing import cast

from slack_bolt import App
from slack_sdk import WebClient

import libs.global_value as g
from integrations import factory
from integrations.slack.adapter import ServiceAdapter
from integrations.slack.events import comparison
from libs.functions import configuration


def main():
    """データ突合処理"""

    if g.args.compar:
        try:
            g.adapter = cast(ServiceAdapter, g.adapter)
            app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.adapter.conf.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.adapter.conf.appclient = app.client
            g.adapter.conf.bot_id = app.client.auth_test()["user_id"]
            configuration.read_memberslist(False)
        except Exception as e:
            raise RuntimeError(e) from e

        adapter_slack = factory.select_adapter("slack", g.cfg)
        adapter_std = factory.select_adapter("standard_io", g.cfg)
        m = adapter_std.parser()
        m.data.channel_id = adapter_slack.functions.get_channel_id()

        count, _ = comparison.data_comparison(m)
        logging.notice(", ".join(f"{k}: {v}" for k, v in count.items()))  # type: ignore
