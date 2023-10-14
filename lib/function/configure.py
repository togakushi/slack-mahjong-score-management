import sys
import configparser

from lib.function import global_value as g


def load(configfile):
    config = configparser.ConfigParser()

    try:
        config.read(configfile, encoding="utf-8")
    except:
        sys.exit()

    g.logging.info(f"configload: {configfile} -> {config.sections()}")
    return(config)


def save(config, configfile):
    with open(configfile, "w") as f:
        config.write(f)


def parameter_load():
    # メンバー登録ファイル
    if g.args.member:
        g.memberfile = g.args.member
    else:
        g.memberfile = g.config["member"].get("filename", "member.ini")

    try:
        g.player_list = configparser.ConfigParser()
        g.player_list.read(g.memberfile, encoding="utf-8")
        g.logging.info(f"configload: {g.memberfile} -> {g.player_list.sections()}")
    except:
        sys.exit(f"{g.memberfile}: file not found")

    g.guest_name = g.config["member"].get("guest_name", "ゲスト")
    g.dbfile = g.config["database"].get("filename", "score.db")


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
        "aggregation_range": [],
        "recursion": True,
        "all_player": False,
        "verbose": False,
    }

    option["aggregation_range"].append(g.config[command].get("aggregation_range", "当日"))
    option["playername_replace"] = g.config[command].getboolean("playername_replace", True)
    option["unregistered_replace"] = g.config[command].getboolean("unregistered_replace", True)
    option["guest_skip"] = g.config[command].getboolean("guest_skip", True)
    option["guest_skip2"] = g.config[command].getboolean("guest_skip2", True)
    option["score_comparisons"] = g.config[command].getboolean("score_comparisons", False)
    option["archive"] = g.config[command].getboolean("archive", False) 
    option["game_results"] = g.config[command].getboolean("game_results", False)
    option["versus_matrix"] = g.config[command].getboolean("versus_matrix", False)
    option["ranked"] = g.config[command].getint("ranked", 3)
    option["stipulated_rate"] = g.config[command].getfloat("stipulated_rate", 0.05)

    return(option)
