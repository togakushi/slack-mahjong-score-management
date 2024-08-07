import sqlite3

import lib.function as f
import lib.command as c
from lib.function import global_value as g


def read_memberslist():
    """
    メンバー/チームリスト読み込み
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    rows = resultdb.execute("select name from member where id=0")
    g.guest_name = rows.fetchone()[0]

    rows = resultdb.execute("select name, member from alias")
    g.member_list = dict(rows.fetchall())

    rows = resultdb.execute("select * from team")
    g.team_list = dict(rows.fetchall())

    resultdb.close()

    g.logging.notice(f"guest_name: {g.guest_name}") # type: ignore
    g.logging.notice(f"member_list: {set(g.member_list.values())}") # type: ignore
    g.logging.notice(f"team_list: {list(g.team_list.values())}") # type: ignore


def get_parameters(argument, command_option):
    """
    オプション、引数から使用する各種パラメータを読み取る

    Parameters
    ----------
    argument : list
        slackから受け取った引数

    command_option : dict
        コマンドオプション

    Returns
    -------
    params : dict
        取得したパラメータ
    """

    target_days, target_player, target_count, command_option = f.common.argument_analysis(argument, command_option)
    starttime, endtime = f.common.scope_coverage(target_days)

    player_name = None
    player_list = {}
    competition_list = {}

    if target_player:
        player_name = target_player[0]
        count = 0
        for name in list(set(target_player)):
            player_list[f"player_{count}"] = name
            count += 1

        # 複数指定
        if len(target_player) >= 1:
            count = 0
            if g.opt.all_player: # 全員対象
                tmp_list = list(set(g.member_list))
            else:
                tmp_list = target_player[1:]

            tmp_list2 = []
            for name in tmp_list: # 名前ブレ修正
                tmp_list2.append(c.member.NameReplace(name, add_mark = False))
            for name in list(set(tmp_list2)): # 集計対象者の名前はリストに含めない
                if name != player_name:
                    competition_list[f"competition_{count}"] = name
                    count += 1

    params = {
        "rule_version": g.rule_version,
        "player_name": player_name,
        "guest_name": g.guest_name,
        "player_list": player_list,
        "competition_list": competition_list,
        "starttime": starttime, # 検索開始日
        "endtime": endtime, # 検索終了日
        "starttime_hm": starttime.strftime("%Y/%m/%d %H:%M"),
        "endtime_hm": endtime.strftime("%Y/%m/%d %H:%M"),
        "starttime_hms": starttime.strftime("%Y/%m/%d %H:%M:%S"),
        "endtime_hms": endtime.strftime("%Y/%m/%d %H:%M:%S"),
        "target_count": target_count,
        "stipulated": g.opt.stipulated,
        "origin_point": g.config["mahjong"].getint("point", 250), # 配給原点
        "return_point": g.config["mahjong"].getint("return", 300), # 返し点
        "group_length": g.opt.group_length,
    }

    if g.opt.search_word:
        params["search_word"] = f"%{g.opt.search_word}%"

    g.logging.trace(f"params: {params}") # type: ignore
    return(params)
