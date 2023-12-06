import lib.command as c
import lib.function as f
import lib.database as d
from lib.function import global_value as g


@g.app.event("message")
def handle_message_events(client, body):
    """
    ゲーム結果をデータベースに反映する
    """

    data = body["event"]
    channel_id = data["channel"]
    if body["authorizations"][0]["is_bot"]:
        bot_id = body["authorizations"][0]["user_id"]
    else:
        bot_id = None

    # DB更新可能チャンネルのポストかチェック
    updatable = False
    if not len(g.channel_limitations) or channel_id in g.channel_limitations.split(","):
        updatable = True

    existence = False # DB投入済みデータ判別フラグ
    if "subtype" in data:
        if data["subtype"] == "message_deleted":
            if updatable:
                d.resultdb_delete(data["deleted_ts"])
            return
        if data["subtype"] == "message_changed":
            data = body["event"]["message"]
            existence = d.ExsistRecord(data["ts"])

    # botが付けたリアクションは判定前に外す
    res = client.reactions_get(
        channel = channel_id,
        timestamp = data["ts"],
    )

    if "reactions" in res["message"]:
        for reaction in res["message"]["reactions"]:
            if reaction["name"] == g.reaction_ok:
                if bot_id in reaction["users"]:
                    client.reactions_remove(
                        channel = channel_id,
                        name = g.reaction_ok,
                        timestamp = data["ts"],
                    )
            if reaction["name"] == g.reaction_ng:
                if bot_id in reaction["users"]:
                    client.reactions_remove(
                        channel = channel_id,
                        name = g.reaction_ng,
                        timestamp = data["ts"],
                    )

    # 結果報告フォーマットに一致したポストの処理
    msg = c.search.pattern(data["text"])
    if msg:
        g.logging.info("post data:[{} {} {}][{} {} {}][{} {} {}][{} {} {}]".format(
            "東家", msg[0], msg[1], "南家", msg[2], msg[3],
            "西家", msg[4], msg[5], "北家", msg[6], msg[7],
            )
        )

        # DB更新
        if existence:
            if updatable:
                d.resultdb_update(msg, data["ts"])
        else:
            if updatable:
                d.resultdb_insert(msg, data["ts"])

        # postされた素点合計が配給原点と同じかチェック
        pointsum = g.config["mahjong"].getint("point", 250) * 4
        score = eval(msg[1]) + eval(msg[3]) + eval(msg[5]) + eval(msg[7])

        if score == pointsum:
            client.reactions_add(
                channel = channel_id,
                name = g.reaction_ok,
                timestamp = data["ts"],
            )
        else:
            msg = f.message.invalid_score(data["user"], score, pointsum)
            f.slack_api.post_message(client, channel_id, msg, data["ts"])
            client.reactions_add(
                channel = channel_id,
                name = g.reaction_ng,
                timestamp = data["ts"],
            )
    else:
        if existence: # DB投入済みデータが削除された場合
            if updatable:
                d.resultdb_delete(data["ts"])
