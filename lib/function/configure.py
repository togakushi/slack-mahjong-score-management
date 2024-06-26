import sqlite3

import lib.function as f
import lib.command as c
from lib.function import global_value as g


def read_memberslist():
    """
    メンバーリスト読み込み
    """

    resultdb = sqlite3.connect(g.database_file, detect_types = sqlite3.PARSE_DECLTYPES)
    resultdb.row_factory = sqlite3.Row

    rows = resultdb.execute("select name from member where id=0")
    g.guest_name = rows.fetchone()[0]

    g.member_list = {}
    rows = resultdb.execute("select name, member from alias")
    for row in rows.fetchall():
        if not row["member"] in g.member_list:
            g.member_list[row["member"]] = row["member"]
        if not row["name"] in g.member_list:
            g.member_list[row["name"]] = row["member"]

    resultdb.close()

    g.logging.notice(f"guest_name: {g.guest_name}") # type: ignore
    g.logging.notice(f"member_list: {set(g.member_list.values())}") # type: ignore


def command_option_initialization(command):
    """
    設定ファイルからコマンドのオプションのデフォルト値を読み込む

    Parameters
    ----------
    command : str
        読み込むコマンド名

    Returns
    -------
    option : dict
        初期化されたオプション
    """

    option = {
        "recursion": True,
        "aggregation_range": [],
        "all_player": False,
        "order": False, # 順位推移グラフ
        "statistics": False, # 統計レポート
        "personal": False, # 個人成績レポート
        "fourfold": False, # 縦持ちデータの直近Nを4倍で取るか
        "stipulated": 0, # 規定打数
        "verbose": False, # 戦績詳細
        "format": g.config["setting"].get("format", "default"),
    }

    option["aggregation_range"].append(g.config[command].get("aggregation_range", "当日"))
    option["unregistered_replace"] = g.config[command].getboolean("unregistered_replace", True)
    option["guest_skip"] = g.config[command].getboolean("guest_skip", True)
    option["guest_skip2"] = g.config[command].getboolean("guest_skip2", True)
    option["score_comparisons"] = g.config[command].getboolean("score_comparisons", False)
    option["game_results"] = g.config[command].getboolean("game_results", False)
    option["versus_matrix"] = g.config[command].getboolean("versus_matrix", False)
    option["ranked"] = g.config[command].getint("ranked", 3)
    option["stipulated_rate"] = g.config[command].getfloat("stipulated_rate", 0.05)

    return(option)


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
            if command_option["all_player"]: # 全員対象
                tmp_list = list(set(g.member_list))
            else:
                tmp_list = target_player[1:]

            tmp_list2 = []
            for name in tmp_list: # 名前ブレ修正
                tmp_list2.append(c.member.NameReplace(name, command_option, add_mark = False))
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
        "stipulated": command_option["stipulated"],
        "origin_point": g.config["mahjong"].getint("point", 250), # 配給原点
        "return_point": g.config["mahjong"].getint("return", 300), # 返し点
    }

    g.logging.trace(f"params: {params}") # type: ignore
    return(params)
