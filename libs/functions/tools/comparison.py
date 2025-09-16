"""
libs/functions/tools/comparison.py
"""

import logging
import os
from configparser import ConfigParser
from typing import cast

from slack_bolt import App
from slack_sdk import WebClient

import libs.global_value as g
from integrations import factory
from integrations.slack.events import comparison
from libs.functions import configuration
from integrations.slack import config


def main():
    """データ突合処理"""

    if g.args.compar:
        try:
            g.app_config = cast(config.AppConfig, factory.load_config("slack", cast(ConfigParser, getattr(g.cfg, "_parser"))))

            app = App(token=os.environ["SLACK_BOT_TOKEN"])
            g.app_config.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
            g.app_config.appclient = app.client
            g.app_config.bot_id = app.client.auth_test()["user_id"]
            configuration.read_memberslist(False)
        except Exception as e:
            raise RuntimeError(e) from e

        api_adapter = factory.select_adapter(g.selected_service)
        m = factory.select_parser("standard_io")
        m.data.channel_id = api_adapter.lookup.get_channel_id()

        count, _ = comparison.data_comparison(m)
        logging.notice(", ".join(f"{k}: {v}" for k, v in count.items()))  # type: ignore
