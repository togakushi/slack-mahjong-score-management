import lib.event as e
from lib.function import global_value as g


@g.app.action("personal_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    result = client.views_publish(
        user_id = body["user"]["id"],
        view = e.PlainText(f"作成中"),
    )

    g.logging.trace(result)

@g.app.action("actionId-personal")
def handle_some_action(ack, body, view, client):
    ack()
    g.logging.trace(body)
    g.logging.info(body)

    b = body['view']['state']['values']
    p1 = list(b['target_player'].values())[0]['selected_option']['value']

    #command_option = f.configure.command_option_initialization("results")

    client.views_publish(
        user_id = body["user"]["id"],
        view = e.PlainText(f"{p1} の成績を集計中…")
    )
