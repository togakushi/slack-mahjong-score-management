"""
lib/event.py
"""

import libs.global_value as g
from libs.functions import events
from libs.functions.events.handler_registry import register


@register
def register_event_handlers(app):
    """イベントAPI"""
    @app.event("message")
    def handle_message_events(body, client):
        """ポストされた内容で処理を分岐

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            body (dict): ポストされたデータ
        """

        g.webclient = client
        events.message_event.main(body)

    @app.command(g.cfg.setting.slash_command)
    def slash_command(ack, body, client):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
            client (slack_bolt.App.client): slack_boltオブジェクト
        """
        g.webclient = client
        events.slash_command.main(ack, body)

    @app.event("app_home_opened")
    def handle_home_events(client, event):
        """ホームタブオープン

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            event (dict): イベント内容
        """

        g.webclient = client
        events.home_tab.main(client, event)
