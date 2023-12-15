import re

import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


@g.app.event("message")
def handle_message_events(client, body):
    """
    ポストされた内容で処理を分岐
    """

    data = body["event"]
    channel_id = data["channel"]
    if "subtype" in body["event"]:
        if body["event"]["subtype"] == "message_deleted":
            user = data["previous_message"]["user"]
            event_ts = data["deleted_ts"]
            text = "delete"
        if body["event"]["subtype"] == "message_changed":
            data = data["message"]
            user = data["user"]
            event_ts = data["ts"]
            text = data["text"]
    else:
        user = data["user"]
        event_ts = data["ts"]
        text = data["text"]

    command = text.split()[0]
    argument = text.split()[1:]

    if body["authorizations"][0]["is_bot"]:
        bot_id = body["authorizations"][0]["user_id"]
    else:
        bot_id = None

    g.logging.info(f"channel_id: {channel_id}, event_ts: {event_ts}, user: {user}, bot_id: {bot_id}")

    # 成績管理系コマンド
    if re.match(rf"^{g.commandword['results']}", text):
        command_option = f.configure.command_option_initialization("results")
        g.logging.info(f"{command}:arg {argument}")
        g.logging.info(f"{command}:opt {command_option}")
        c.results.slackpost(client, channel_id, event_ts, argument, command_option)
        return
    if re.match(rf"^{g.commandword['graph']}", text):
        command_option = f.configure.command_option_initialization("graph")
        g.logging.info(f"{command}:arg {argument}")
        g.logging.info(f"{command}:opt {command_option}")
        c.graph.slackpost(client, channel_id, argument, command_option)
        return
    if re.match(rf"^{g.commandword['ranking']}", text):
        command_option = f.configure.command_option_initialization("ranking")
        g.logging.info(f"{command}:arg {argument}")
        g.logging.info(f"{command}:opt {command_option}")
        c.ranking.slackpost(client, channel_id, argument, command_option)
        return
    if re.match(rf"{g.commandword['record']}", text):
        command_option = f.configure.command_option_initialization("record")
        g.logging.info(f"{command}:arg {argument}")
        g.logging.info(f"{command}:opt {command_option}")
        c.record.slackpost(client, channel_id, argument, command_option)
        return

    # データベース関連コマンド
    if re.match(rf"^{g.commandword['check']}", text):
        command_option = f.configure.command_option_initialization("record")
        command_option["unregistered_replace"] = False # ゲスト無効
        g.logging.info(f"{command}:arg {argument}")
        g.logging.info(f"{command}:opt {command_option}")
        d.comparison.slackpost(client, channel_id, event_ts, argument, command_option)
        return
    if re.match(rf"^Reminder: {g.commandword['check']}$", text): # Reminderによる突合
        command_option = f.configure.command_option_initialization("record")
        command_option["unregistered_replace"] = False # ゲスト無効
        g.logging.info(f'Reminder: {g.commandword["check"]}')
        d.comparison.slackpost(client, channel_id, event_ts, None, command_option)
        return

    # botが付けたリアクションは判定前に外す
    reactions_check = True
    if "subtype" in body["event"]:
        if body["event"]["subtype"] == "message_deleted":
            reactions_check = False

    if reactions_check:
        res = client.reactions_get(
            channel = channel_id,
            timestamp = event_ts,
        )
        if "reactions" in res["message"]:
            for reaction in res["message"]["reactions"]:
                if reaction["name"] == g.reaction_ok:
                    if bot_id in reaction["users"]:
                        client.reactions_remove(
                            channel = channel_id,
                            name = g.reaction_ok,
                            timestamp = event_ts,
                        )
                if reaction["name"] == g.reaction_ng:
                    if bot_id in reaction["users"]:
                        client.reactions_remove(
                            channel = channel_id,
                            name = g.reaction_ng,
                            timestamp = event_ts,
                        )

    updatable = False # DB更新可能チャンネルのポストかチェック
    if not len(g.channel_limitations) or channel_id in g.channel_limitations.split(","):
        updatable = True

    existence = False # DB投入済みデータ判別フラグ
    if "subtype" in body["event"]:
        if body["event"]["subtype"] == "message_deleted":
            if updatable:
                d.resultdb_delete(data["deleted_ts"])
            return
        if body["event"]["subtype"] == "message_changed":
            existence = d.ExsistRecord(event_ts)

    # 結果報告フォーマットに一致したポストの処理
    msg = c.search.pattern(text)
    if msg:
        f.check_score(client, channel_id, event_ts, user, msg)

        # DB更新
        if updatable:
            if existence:
                d.resultdb_update(msg, event_ts)
            else:
                d.resultdb_insert(msg, event_ts)

    else:
        if updatable and existence: # DB投入済みデータが削除された場合
            d.resultdb_delete(event_ts)
