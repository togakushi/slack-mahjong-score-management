import re

import command as c
import function as f
from function import global_value as g

commandword = g.config["versus"].get("commandword", "御無礼対戦")

# イベントAPI
@g.app.message(re.compile(rf"^{commandword}"))
def handle_versus_evnts(client, context, body):
    command = body["event"]["text"].split()[0]
    argument = body["event"]["text"].split()[1:]

    if not re.match(rf"^{commandword}$", command):
        return

    command_option = f.configure.command_option_initialization("versus")
    g.logging.info(f"[{command}] {command_option} {argument}")
    slackpost(client, context.channel_id, argument, command_option)


def slackpost(client, channel, argument, command_option):
    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    msg = getdata(starttime, endtime, target_player, command_option)
    f.slack_api.post_text(client, channel, "", msg)

def getdata(starttime, endtime, target_player, command_option):
    """
    xxxを取得

    Parameters
    ----------
    starttime : date
        集計開始日時

    endtime : date
        集計終了日時

    target_player : list
        集計対象プレイヤー（空のときは全プレイヤーを対象にする）

    command_option : dict
        コマンドオプション

    Returns
    -------
    msg : text
        slackにpostする内容
    """

    g.logging.info(f"[versus] {command_option}")
    results = c.search.getdata(command_option)

    if len(target_player) == 0:
        return("プレイヤーを1名以上指定してください。")

    game_count = 0
    first_game = False
    last_game = False
    versus_matrix = {}
    for i in results.keys():
        if starttime < results[i]["日付"] and endtime > results[i]["日付"]:
            myrank = None
            count_flag = False
            for wind in ("東家", "南家", "西家", "北家"):
                if results[i][wind]["name"] == target_player[0]:
                    myrank = results[i][wind]["rank"]
            if myrank:
                for wind in ("東家", "南家", "西家", "北家"):
                    vs_player = results[i][wind]["name"]
                    vs_rank = results[i][wind]["rank"]
                    if not command_option["unregistered_replace"]:
                        if not c.member.ExsistPlayer(vs_player):
                            vs_player = vs_player + "(※)"

                    if len(target_player) == 1: # 全員分
                        if vs_player == target_player[0]: # 自分の成績は比較しない
                            continue
                        count_flag = True
                        if not vs_player in versus_matrix.keys():
                            versus_matrix[vs_player] = {"win":0, "lose":0}
                        if myrank < vs_rank:
                            versus_matrix[vs_player]["win"] += 1
                        else:
                            versus_matrix[vs_player]["lose"] += 1

                    elif vs_player in target_player[1:]: # 指定プレイヤーのみ
                        count_flag = True
                        if not vs_player in versus_matrix.keys():
                            versus_matrix[vs_player] = {"win":0, "lose":0}
                        if myrank < vs_rank:
                            versus_matrix[vs_player]["win"] += 1
                        else:
                            versus_matrix[vs_player]["lose"] += 1

            if count_flag:
                if not first_game:
                    first_game = results[i]["日付"]
                last_game = results[i]["日付"]
                game_count += 1


    msg = ""
    padding = max([f.translation.len_count(x) for x in versus_matrix.keys()])
    header = "## {}の対戦結果 ： 勝率 ##\n".format(target_player[0])
    for i in versus_matrix.keys():
        msg += "{} {}：{:>7.2%} ({:3}戦{:3}勝{:3}敗)\n".format(
            i, " " * (padding - f.translation.len_count(i)),
            versus_matrix[i]["win"] / (versus_matrix[i]["win"] + versus_matrix[i]["lose"]),
            versus_matrix[i]["win"] + versus_matrix[i]["lose"],
            versus_matrix[i]["win"],
            versus_matrix[i]["lose"],
        )

    footer = "-" * 5 + "\n"
    footer += f"検索範囲：{starttime.strftime('%Y/%m/%d %H:%M')} ～ {endtime.strftime('%Y/%m/%d %H:%M')}\n"
    footer += f"最初のゲーム：{first_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"最後のゲーム：{last_game.strftime('%Y/%m/%d %H:%M:%S')}\n"
    footer += f"総ゲーム回数： {game_count} 回\n"
    remarks = []
    if not command_option["playername_replace"]:
        remarks.append("名前ブレ修正なし")
    if not command_option["guest_skip"]:
        remarks.append("2ゲスト戦を含む")
    if not command_option["unregistered_replace"]:
        remarks.append("ゲスト置換なし(※：未登録プレイヤー)")
    if remarks:
        footer += f"特記事項：" + "、".join(remarks)

    return(header + msg + footer)
