import lib.command as c
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
            command_option = f.configure.command_option_initialization("results")
            g.logging.info(f"subcommand({subcom}): {argument} {command_option}")
            c.results.slackpost(client, user_id, event_ts, argument, command_option)
            return

        if subcom.lower() in subcommand_list("graph"):
            command_option = f.configure.command_option_initialization("graph")
            g.logging.info(f"subcommand({subcom}): {argument} {command_option}")
            c.graph.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in subcommand_list("record"):
            command_option = f.configure.command_option_initialization("record")
            g.logging.info(f"subcommand({subcom}): {argument} {command_option}")
            c.record.slackpost(client, user_id, argument, command_option)
            return

        if subcom.lower() in subcommand_list("ranking"):
            command_option = f.configure.command_option_initialization("ranking")
            g.logging.info(f"subcommand({subcom}): {argument} {command_option}")
            c.ranking.slackpost(client, user_id, argument, command_option)
            return

        # メンバー管理系コマンド
        if subcom.lower() in subcommand_list("member"):
            title, msg = c.member.GetList()
            f.slack_api.post_text(client, user_id, event_ts, title, msg)
            return

        if subcom.lower() in subcommand_list("add"):
            msg = c.member.Append(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        if subcom.lower() in subcommand_list("del"):
            msg = c.member.Remove(argument)
            f.slack_api.post_message(client, user_id, msg)
            return

        #if subcom.lower() in subcommand_list("export"):
        #    command_option = f.configure.command_option_initialization("record") # 一旦recordに合わせる
        #    g.logging.info(f"[subcommand({subcom})] {argument} {command_option}")
        #    exportfile = f.score.csv_export(argument, command_option)
        #    f.slack_api.post_message(client, user_id, f"{exportfile}に保存しました。")
        #    return

    f.slack_api.post_message(client, user_id, f.message.help(body["command"]))
