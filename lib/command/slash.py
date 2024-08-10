import lib.command as c
import lib.database as d
import lib.function as f
from lib.function import global_value as g


class CommandCheck(str):
    """
    キーワードがサブコマンドかチェックする(match専用)
    """

    def __init__(self, command_name: str):
        self.command_name = command_name

    def __eq__(self, chk_pattern):
        commandlist = g.config["alias"].get(chk_pattern, "")
        commandlist = [chk_pattern] + [x for x in commandlist.split(",") if x]

        if self.command_name in commandlist:
            return (True)

        return (False)


@g.app.command(g.slash_command)
def slash_command(ack, body, client):
    ack()
    g.logging.trace(f"{body}")  # type: ignore
    channel_id = body["channel_id"]
    event_ts = 0

    if body["text"]:
        subcom = body["text"].split()[0].lower()
        argument = body["text"].split()[1:]

        match CommandCheck(subcom):
            # 成績管理系コマンド
            case "results":
                c.results.slackpost.main(client, channel_id, argument)
            case "graph":
                c.graph.slackpost.main(client, channel_id, argument)
            case "ranking":
                c.ranking.slackpost.main(client, channel_id, argument)
            case "report":
                c.report.slackpost.main(client, channel_id, argument)

            # データベース関連コマンド
            case "check":
                d.comparison.main(client, channel_id, event_ts)
            case "download":
                f.slack_api.post_fileupload(
                    client, channel_id,
                    "resultdb", g.database_file
                )

            # メンバー管理系コマンド
            case "member":
                title, msg = c.member.Getmemberslist()
                f.slack_api.post_text(
                    client, channel_id, event_ts,
                    title, msg
                )
            case "add":
                msg = c.member.MemberAppend(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case "del":
                msg = c.member.MemberRemove(argument)
                f.slack_api.post_message(client, channel_id, msg)

            # チーム管理系コマンド
            case "team_create":
                msg = c.team.create(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case "team_del":
                msg = c.team.delete(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case "team_add":
                msg = c.team.append(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case "team_remove":
                msg = c.team.remove(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case "team_list":
                msg = c.team.list()
                f.slack_api.post_message(client, channel_id, msg)
            case "team_clear":
                msg = c.team.clear()
                f.slack_api.post_message(client, channel_id, msg)

            # その他
            case _:
                f.slack_api.post_message(
                    client, channel_id,
                    f.message.help(body["command"])
                )
