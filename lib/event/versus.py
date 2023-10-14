import lib.event as e
from lib.function import global_value as g


@g.app.action("versus_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    result = client.views_publish(
        user_id = body["user"]["id"],
        #view = e.DispVersusMenu(),
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
    p2 = list(b['vs_player'].values())[0]['selected_option']['value']

    #command_option = f.configure.command_option_initialization("results")

    client.views_publish(
        user_id = body["user"]["id"],
        view = e.PlainText(f"{p1} vs {p2} の直接対戦を集計中…"),
    )


@g.app.action("actionId-test")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    result = client.views_open(
        user_id = body["user"]["id"],
        trigger_id=body["trigger_id"],

        view = {
            "type": "modal",
            "callback_id": "modal-id",
            "title": {
                "type": "plain_text",
                "text": "検索範囲指定"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "element": {
                        "type": "datepicker",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "datepicker-action1"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Label"
                    }
                },
                {
                    "type": "input",
                    "element": {
                        "type": "datepicker",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a date"
                        },
                        "action_id": "datepicker-action2"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Label"
                    }
                }
            ]
        }
    )

    g.logging.trace(result)

@g.app.view("modal-id")
def handle_view_submission(ack, view):
    ack()
    # state.values.{block_id}.{action_id}
    g.logging.info(f'[sub] {view["state"]["values"]}')

    print(view)
    return(view["state"]["values"])
