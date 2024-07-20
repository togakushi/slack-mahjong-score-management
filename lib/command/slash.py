import lib.command as c
import lib.database as d
import lib.function as f
from lib.function import global_value as g


def subcommand_list(subcommand):
    """
    サブコマンドのリストを返す

    Parameters
    ----------
    subcommand : str
        サブコマンド名

    Returns
    -------
    commandlist : list
        エイリアスを含めたサブコマンドのリスト
    """

    commandlist = g.config["alias"].get(subcommand, "")
    commandlist = [subcommand] + [x for x in commandlist.split(",") if x]

    return(commandlist)


@g.app.command(g.slash_command)
def slash_command(ack, body, client):
    ack()
    g.logging.trace(f"{body}") # type: ignore
    channel_id = body["channel_id"]
    event_ts = 0

    if body["text"]:
        subcom = body["text"].split()[0].lower()
        argument = body["text"].split()[1:]

        match subcom:
            # 成績管理系コマンド
            case subcom if subcom in subcommand_list("results"):
                g.logging.info(f"subcommand({subcom}): {argument}")
                c.results.slackpost.main(client, channel_id, argument)
            case subcom if subcom in subcommand_list("graph"):
                g.logging.info(f"subcommand({subcom}): {argument}")
                c.graph.slackpost.main(client, channel_id, argument)
            case subcom if subcom in subcommand_list("ranking"):
                g.logging.info(f"subcommand({subcom}): {argument}")
                c.ranking.slackpost.main(client, channel_id, argument)
            case subcom if subcom in subcommand_list("report"):
                g.logging.info(f"subcommand({subcom}): {argument}")
                c.report.slackpost.main(client, channel_id, argument)

            # データベース関連コマンド
            case subcom if subcom in subcommand_list("check"):
                g.logging.info(f"subcommand({subcom}): {argument}")
                d.comparison.main(client, channel_id, event_ts, argument)
            case subcom if subcom in subcommand_list("download"):
                g.logging.info(f"subcommand({subcom}): {g.database_file}")
                f.slack_api.post_fileupload(client, channel_id, "resultdb", g.database_file)

            # メンバー管理系コマンド
            case subcom if subcom in subcommand_list("member"):
                title, msg = c.member.Getmemberslist()
                f.slack_api.post_text(client, channel_id, event_ts, title, msg)
            case subcom if subcom in subcommand_list("add"):
                msg = c.member.MemberAppend(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case subcom if subcom in subcommand_list("del"):
                msg = c.member.MemberRemove(argument)
                f.slack_api.post_message(client, channel_id, msg)

            # チーム管理系コマンド
            case subcom if subcom in subcommand_list("team_del"):
                msg = c.team.delete(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case subcom if subcom in subcommand_list("team_add"):
                msg = c.team.append(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case subcom if subcom in subcommand_list("team_remove"):
                msg = c.team.remove(argument)
                f.slack_api.post_message(client, channel_id, msg)
            case subcom if subcom in subcommand_list("team_list"):
                msg = c.team.list()
                f.slack_api.post_message(client, channel_id, msg)
            case subcom if subcom in subcommand_list("team_clear"):
                msg = c.team.clear()
                f.slack_api.post_message(client, channel_id, msg)

            # その他
            case _:
                f.slack_api.post_message(client, channel_id, f.message.help(body["command"]))
