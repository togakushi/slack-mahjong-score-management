import lib.event as e
from lib.function import global_value as g


@g.app.action("ranking_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    result = client.views_publish(
        user_id = body["user"]["id"],
        view = e.PlainText(f"作成中")
    )

    g.logging.trace(result)
