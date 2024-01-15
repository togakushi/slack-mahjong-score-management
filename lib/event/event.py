import re
import sqlite3

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


def param_retrieving(parameter, data):
    if "user" in data:
        parameter["user"] = data["user"]
    if "ts" in data:
        parameter["event_ts"] = data["ts"]
    if "text" in data:
        parameter["text"] = data["text"]
    if "thread_ts" in data:
        parameter["thread_ts"] = data["thread_ts"]

    return(parameter)


# イベントAPI
@g.app.event("message")
def handle_message_events(client, body):
    """
    ポストされた内容で処理を分岐
    """

    g.logging.trace(body)

    # 各種パラメータ取得
    existence = False
    parameter = {
        "status": "message_append",
        "channel_id": body["event"]["channel"],
        "user": None,
        "bot_id": None,
        "event_ts": None,
        "thread_ts": None,
        "text": "",
    }

    if "subtype" in body["event"]:
        match body["event"]["subtype"]:
            case "message_changed":
                parameter["status"] = "message_changed"
                parameter = param_retrieving(parameter, body["event"]["message"])
                existence = d.ExsistRecord(parameter["event_ts"])
            case "message_deleted":
                parameter["status"] = "message_deleted"
                parameter = param_retrieving(parameter, body["event"]["previous_message"])
                parameter["event_ts"] = body["event"]["deleted_ts"]
            case _:
                parameter = param_retrieving(parameter, body["event"])
    else:
        parameter = param_retrieving(parameter, body["event"])

    if body["authorizations"][0]["is_bot"]:
        parameter["bot_id"] = body["authorizations"][0]["user_id"]

    argument = parameter["text"].split()[1:] # 最初のスペース以降はコマンド引数扱い

    # DB更新可能チャンネルのポストかチェック
    if not len(g.channel_limitations) or parameter["channel_id"] in g.channel_limitations.split(","):
        updatable = True
    else:
        updatable = False

    g.logging.info("status: {}, event_ts: {}, thread_ts: {}, updatable: {}".format(
        parameter["status"],
        parameter["event_ts"],
        parameter["thread_ts"],
        updatable,
    ))

    # ヘルプ
    if re.match(rf"^{g.commandword['help']}", parameter["text"]):
        msg = f.help_message()
        f.slack_api.post_message(client, parameter["channel_id"], msg, parameter["event_ts"])

        title, msg = c.Getmemberslist()
        f.slack_api.post_text(client, parameter["channel_id"], parameter["event_ts"], title, msg)
        return

    # 成績管理系コマンド
    if re.match(rf"^{g.commandword['results']}", parameter["text"]):
        c.results.__main__.slackpost(client, parameter["channel_id"], argument)
        return
    if re.match(rf"^{g.commandword['graph']}", parameter["text"]):
        c.graph.__main__.slackpost(client, parameter["channel_id"], argument)
        return
    if re.match(rf"^{g.commandword['ranking']}", parameter["text"]):
        c.ranking.slackpost(client, parameter["channel_id"], argument)
        return
    if re.match(rf"^{g.commandword['report']}", parameter["text"]):
        c.report.__main__.slackpost(client, parameter["channel_id"], argument)
        return

    # データベース関連コマンド
    if re.match(rf"^{g.commandword['check']}", parameter["text"]):
        d.comparison.slackpost(client, parameter["channel_id"], parameter["event_ts"], argument)
        return
    if re.match(rf"^Reminder: {g.commandword['check']}$", parameter["text"]): # Reminderによる突合
        g.logging.info(f'Reminder: {g.commandword["check"]}')
        d.comparison.slackpost(client, parameter["channel_id"], parameter["event_ts"], None)
        return

    # 追加メモ
    if re.match(rf"^{g.commandword['remarks_word']}", parameter["text"]) and parameter["thread_ts"]:
        if d.ExsistRecord(parameter["thread_ts"]) and updatable:
            command_option = f.configure.command_option_initialization("results")
            command_option["unregistered_replace"] = False # ゲスト無効
            resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
            match parameter["status"]:
                case "message_append":
                    for name, val in zip(argument[0::2], argument[1::2]):
                        g.logging.info(f"insert: {name}, {val}")
                        resultdb.execute(d.sql_remarks_insert, (
                            parameter["thread_ts"],
                            parameter["event_ts"],
                            c.NameReplace(name, command_option),
                            val,
                        ))
                case "message_changed":
                    resultdb.execute(d.sql_remarks_delete_one, (parameter["event_ts"],))
                    for name, val in zip(argument[0::2], argument[1::2]):
                        g.logging.info(f"update: {name}, {val}")
                        resultdb.execute(d.sql_remarks_insert, (
                            parameter["thread_ts"],
                            parameter["event_ts"],
                            c.NameReplace(name, command_option),
                            val,
                        ))
                case "message_deleted":
                    g.logging.info(f"delete one")
                    resultdb.execute(d.sql_remarks_delete_one, (parameter["event_ts"],))

            resultdb.commit()
            resultdb.close()

    # botが付けたリアクションは判定前に外す
    if parameter["status"] == "message_changed":
        res = client.reactions_get(
            channel = parameter["channel_id"],
            timestamp = parameter["event_ts"],
        )
        if "reactions" in res["message"]:
            for reaction in res["message"]["reactions"]:
                if reaction["name"] == g.reaction_ok:
                    if parameter["bot_id"] in reaction["users"]:
                        client.reactions_remove(
                            channel = parameter["channel_id"],
                            name = g.reaction_ok,
                            timestamp = parameter["event_ts"],
                        )
                if reaction["name"] == g.reaction_ng:
                    if parameter["bot_id"] in reaction["users"]:
                        client.reactions_remove(
                            channel = parameter["channel_id"],
                            name = g.reaction_ng,
                            timestamp = parameter["event_ts"],
                        )

    # 結果報告フォーマットに一致したポストの処理
    msg = f.search.pattern(parameter["text"])
    if msg:
        if not parameter["status"] == "message_deleted":
            f.check_score(client, parameter["channel_id"], parameter["event_ts"], parameter["user"], msg)
        if updatable:
            match parameter["status"]:
                case "message_append":
                    d.resultdb_insert(msg, parameter["event_ts"])
                case "message_changed":
                    if existence:
                        d.resultdb_update(msg, parameter["event_ts"])
                    else:
                        d.resultdb_insert(msg, parameter["event_ts"])
                case "message_deleted":
                    d.resultdb_delete(parameter["event_ts"])
    else:
        if updatable and existence: # データベース投入済みデータが削除された場合
            d.resultdb_delete(parameter["event_ts"])
