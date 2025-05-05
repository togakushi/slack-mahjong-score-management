"""
lib/event.py
"""

import libs.global_value as g
from libs.functions import events


@events.handler_registry.register
def register_event_handlers(app):
    """イベントAPI"""
    @app.event("message")
    def handle_message_events(client, body):
        """ポストされた内容で処理を分岐

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            body (dict): ポストされたデータ
        """

        events.message_event.main(client, body)

    @app.command(g.cfg.setting.slash_command)
    def slash_command(ack, body, client):
        """スラッシュコマンド

        Args:
            ack (_type_): ack
            body (dict): ポストされたデータ
            client (slack_bolt.App.client): slack_boltオブジェクト
        """

        events.slash_command.main(ack, body, client)

    @app.event("app_home_opened")
    def handle_home_events(client, event):
        """ホームタブオープン

        Args:
            client (slack_bolt.App.client): slack_boltオブジェクト
            event (dict): イベント内容
        """

        events.home_tab.main(client, event)
