import lib.command as c
import lib.function as f
import lib.event as e
from lib.function import global_value as g


@g.app.action("summary_menu")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    result = client.views_publish(
        user_id = body["user"]["id"],
        view = e.DispSummryMenu(),
    )

    g.logging.trace(result)

@g.app.action("actionId-search")
def handle_some_action(ack, body, client):
    ack()
    g.logging.trace(body)

    user_id = body["user"]["id"]
    sday = body["view"]["state"]["values"]["bid-sday"]["aid-sday"]["selected_date"]
    eday = body["view"]["state"]["values"]["bid-eday"]["aid-eday"]["selected_date"]
    selected_options = body["view"]["state"]["values"]["bid-checkboxes"]["aid-checkboxes"]["selected_options"]

    client.views_publish(
        user_id = user_id,
        view = e.PlainText(f"{sday} ～ {eday} の結果を集計中…"),
    )

    command_option = f.configure.command_option_initialization("results")

    if sday != None:
        command_option["aggregation_range"] = []
        command_option["aggregation_range"].append(sday.replace("-",""))
    if eday != None:
        command_option["aggregation_range"].append(eday.replace("-",""))

    for i in range(len(selected_options)):
        flag = selected_options[i]["value"]
        if flag == "unregistered_replace":
            command_option[flag] = False
        if flag == "archive":
            command_option[flag] = True

    g.logging.info(command_option)
    target_days, target_player, target_count, command_option = f.common.argument_analysis("", command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    msg = ""
    if starttime and endtime:
        msg = c.results.summary(starttime, endtime, target_player, target_count, command_option)
        f.slack_api.post_text(client, user_id, False, "", msg)

    client.views_publish(
        user_id = user_id,
        view = e.PlainText(f"集計完了"),
    )
