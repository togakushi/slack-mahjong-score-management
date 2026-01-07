"""
libs/functions/tools/comparison.py
"""

import os
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from integrations import factory
from integrations.slack.events import comparison
from libs.data import lookup

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter as discord_adapter
    from integrations.protocols import MessageParserProtocol
    from integrations.slack.adapter import ServiceAdapter as slack_adapter
    from libs.datamodels import ComparisonResults


def main():
    """データ突合処理"""

    g.cfg.initialization()

    # 結果の出力先(standard_io)
    adapter_std = factory.select_adapter("standard_io", g.cfg)
    m = adapter_std.parser()

    # 連携サービス切替
    match g.adapter.interface_type:
        case "slack":
            g.adapter = factory.select_adapter(g.adapter.interface_type, g.cfg)
            slack_comparison(m)
        case "discord":
            g.adapter = factory.select_adapter(g.adapter.interface_type, g.cfg)
            discord_comparison(m)
        case _:
            return

    if isinstance(m.status.message, str):
        print(m.status.message)
    else:
        print(cast("ComparisonResults", m.status.message).output("summary"))


def slack_comparison(m: "MessageParserProtocol"):
    """突合処理(slack)

    Args:
        m (MessageParserProtocol): メッセージデータ

    Raises:
        ModuleNotFoundError: ライブラリ未インストール
        RuntimeError: 接続エラー
    """

    try:
        from slack_bolt import App
        from slack_sdk import WebClient
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(err.msg) from None

    g.adapter = cast("slack_adapter", g.adapter)

    try:
        app = App(token=os.environ["SLACK_BOT_TOKEN"])
        g.adapter.api.webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
        g.adapter.api.appclient = app.client
    except Exception as err:
        raise RuntimeError(err) from err

    g.adapter.conf.bot_id = app.client.auth_test()["user_id"]
    m.data.channel_id = g.adapter.functions.get_channel_id()

    lookup.read_memberslist()
    comparison.main(m)


def discord_comparison(m: "MessageParserProtocol"):
    """突合処理(discord)

    Args:
        m (MessageParserProtocol): メッセージデータ
    """

    g.adapter = cast("discord_adapter", g.adapter)

    m.status.message = "未実装"
