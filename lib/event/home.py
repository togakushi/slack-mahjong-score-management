import command as c
import function as f
from function import global_value as g


@g.app.event("app_home_opened")
def handle_home_events(client, event):
    user_id = event["user"]

    result = client.views_publish(
        user_id = user_id,
        view = {
            "type": "home",
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "全体成績サマリ"
                            },
                            "value": "click_summary_menu",
                            "action_id": "actionId-summary_menu"
                        }
                    ]
                }
            ]
        }
    )

    g.logging.trace(result)
