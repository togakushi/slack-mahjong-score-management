import lib.command as c
import lib.database as d
import lib.function as f
from lib.function import global_value as g

commandname = g.config["setting"].get("slash_commandname", "/mahjong")
g.logging.info(f"slash command: {commandname}")


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


@g.app.command(commandname)
def slash_command(ack, body, client):
    ack()
    g.logging.trace(f"{body}")
    user_id = body["user_id"]
    event_ts = 0

    if body["text"]:
        subcom = body["text"].split()[0]
        argument = body["text"].split()[1:]

        # 成績管理系コマンド
        if subcom.lower() in subcommand_list("results"):
            g.logging.info(f"subcommand({subcom}): {argument}")
            c.results.__main__.slackpost(client, user_id, argument)
            return

        if subcom.lower() in subcommand_list("graph"):
            g.logging.info(f"subcommand({subcom}): {argument}")
            c.graph.__main__.slackpost(client, user_id, argument)
            return

        if subcom.lower() in subcommand_list("ranking"):
            g.logging.info(f"subcommand({subcom}): {argument}")
            c.ranking.slackpost(client, user_id, argument)
            return

        if subcom.lower() in subcommand_list("report"):
            g.logging.info(f"subcommand({subcom}): {argument}")
            c.report.__main__.slackpost(client, user_id, argument)
            return

        # データベース関連コマンド
        if subcom.lower() in subcommand_list("check"):
            g.logging.info(f"subcommand({subcom}): {argument}")
            d.comparison.slackpost(client, user_id, event_ts, argument)
            return

        if subcom.lower() in subcommand_list("download"):
            g.logging.info(f"subcommand({subcom}): {g.database_file}")
            f.slack_api.post_fileupload(client, user_id, "resultdb", g.database_file)
            return

        # メンバー管理系コマンド
        if subcom.lower() in subcommand_list("member"):
            title, msg = c.Getmemberslist()
            f.slack_api.post_text(client, user_id, event_ts, title, msg)
            return

        if subcom.lower() in subcommand_list("add"):
            msg = c.MemberAppend(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in subcommand_list("del"):
            msg = c.MemberRemove(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

    f.slack_api.post_message(client, user_id, f.message.help(body["command"]))
