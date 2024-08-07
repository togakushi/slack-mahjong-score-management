import argparse
import configparser
import logging
import sys
import os

from functools import partial
from datetime import datetime
from dateutil.relativedelta import relativedelta

from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import lib.function as f


class command_option:
    def __init__(self) -> None:
        self.initialization("DEFAULT")

    def initialization(self, command, _argument = ""):
        self.__dict__.clear()
        if not command in config.sections():
            command = "DEFAULT"

        self.command: str = command
        self.recursion: bool = True
        self.aggregation_range: list = []
        self.aggregation_range.append(config[command].get("aggregation_range", "当日"))
        self.target_days: list = []
        self.all_player: bool = False
        self.order: bool = False # 順位推移グラフ
        self.statistics: bool = False # 統計レポート
        self.personal: bool = False # 個人成績レポート
        self.fourfold: bool = False # 縦持ちデータの直近Nを4倍で取るか
        self.stipulated: int = 0 # 規定打数
        self.target_count: int = 0
        self.verbose: bool = False # 戦績詳細
        self.team_total: bool = False # チーム集計
        self.friendly_fire: bool = config["team"].getboolean("friendly_fire", False)
        self.unregistered_replace: bool = config[command].getboolean("unregistered_replace", True)
        self.guest_skip: bool = config[command].getboolean("guest_skip", True)
        self.guest_skip2: bool = config[command].getboolean("guest_skip2", True)
        self.score_comparisons: bool = config[command].getboolean("score_comparisons", False)
        self.game_results: bool = config[command].getboolean("game_results", False)
        self.versus_matrix: bool = config[command].getboolean("versus_matrix", False)
        self.ranked: int = config[command].getint("ranked", 3)
        self.stipulated_rate: float = config[command].getfloat("stipulated_rate", 0.05)
        self.format: str = config["setting"].get("format", "default")
        self.filename: str = ""
        self.daily: bool = False
        self.group_length: int = config["comment"].getint("group_length", 0)
        self.search_word: str = config["comment"].get("search_word", None)

        if _argument:
            self.update(_argument)

    def update(self, argument: list):
        _, _, _, new = f.common.argument_analysis(argument)
        self.__dict__.update(zip(new.keys(), new.values()))

class parameters:
    def __init__(self) -> None:
        self.initialization()

    def initialization(self):
        self.__dict__.clear()

        self.argument = None
        self.rule_version = config["mahjong"].get("rule_version", "")
        self.origin_point = config["mahjong"].getint("point", 250) # 配給原点
        self.return_point = config["mahjong"].getint("return", 300) # 返し点
        self.player_name = None
        self.guest_name = None
        self.player_list: dict = {}
        self.competition_list: dict = {}
        self.starttime = None
        self.starttime_hm = None
        self.starttime_hms = None
        self.endtime = None
        self.endtime_hm = None
        self.endtime_hms = None
        self.target_count: int = 0

    def update(self, _argument: list, _option: dict):
        self.initialization()
        new = f.configure.get_parameters(_argument, _option)
        self.__dict__.update(zip(new.keys(), new.values()))
        self.argument = _argument

    def to_dict(self):
        tmp_dict = self.__dict__
        if self.player_list:
            tmp_dict.update(self.player_list)
        if self.competition_list:
            tmp_dict.update(self.competition_list)

        return(tmp_dict)


def parser():
    p = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        add_help = True,
    )

    p.add_argument(
        "--debug",
        action = "store_true",
        help = "デバッグ情報表示",
    )

    p.add_argument(
        "--verbose",
        action = "store_true",
        help = "詳細デバッグ情報表示",
    )

    p.add_argument(
        "--moderate",
        action = "store_true",
        help = "ログレベルがエラー以下のもを非表示",
    )

    p.add_argument(
        "--notime",
        action = "store_true",
        help = "ログフォーマットから日時を削除",
    )

    p.add_argument(
        "-c", "--config",
        default = "config.ini",
        metavar = "config.ini",
        help = "設定ファイル",
    )

    p.add_argument(
        "-t", "--testcase",
        metavar = "testcase.ini",
        help = "動作テスト用",
    )

    return(p.parse_args())

### ログレベル追加 ###
# TRACE
logging.TRACE = 19  # type: ignore
logging.trace = partial(logging.log, logging.TRACE) # type: ignore
logging.addLevelName(logging.TRACE, "TRACE") # type: ignore
# NOTICE
logging.NOTICE = 25 # type: ignore
logging.notice = partial(logging.log, logging.NOTICE) # type: ignore
logging.addLevelName(logging.NOTICE, "NOTICE") # type: ignore

### コマンドラインオプション解析 ###
args = parser()

if args.notime:
    fmt = "[%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"
else:
    fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level = logging.TRACE, format = fmt) # type: ignore
    else:
        print("DEBUG MODE")
        logging.basicConfig(level = logging.INFO, format = fmt)
else:
    if args.moderate:
        logging.basicConfig(level = logging.WARNING, format = fmt)
    else:
        logging.basicConfig(level = logging.NOTICE, format = fmt) # type: ignore

### 設定ファイル読み込み ###
try:
    config = configparser.ConfigParser()
    config.read(args.config, encoding="utf-8")
    logging.notice(f"config read: {args.config} -> {config.sections()}") # type: ignore
except:
    sys.exit()

# 必須セクションチェック
for x in ("mahjong", "setting"):
    if not x in config.sections():
        sys.exit()

# オプションセクションチェック
for x in ("results", "graph", "ranking", "report", "member", "team", "database", "comment", "help"):
    if not x in config.sections():
        config.add_section(x)

commandword = { # チャンネル内呼び出しキーワード
    "results": config["results"].get("commandword", "麻雀成績"),
    "graph": config["graph"].get("commandword", "麻雀グラフ"),
    "ranking": config["ranking"].get("commandword", "麻雀ランキング"),
    "report": config["report"].get("commandword", "麻雀成績レポート"),
    "member": config["member"].get("commandword", "メンバー一覧"),
    "team": config["team"].get("commandword", "チーム一覧"),
}

rule_version = config["mahjong"].get("rule_version", "")
slash_command = config["setting"].get("slash_commandname", "/mahjong")
guest_mark = config["setting"].get("guest_mark", "※")
reaction_ok = config["setting"].get("reaction_ok", "ok")
reaction_ng = config["setting"].get("reaction_ng", "ng")
font_file = config["setting"].get("font_file", "ipaexg.ttf")
work_dir = config["setting"].get("work_dir", "work")
ignore_userid = [x.strip() for x in config["setting"].get("ignore_userid", "").split(",")]
commandword.update(remarks_word = config["setting"].get("remarks_word", "麻雀成績メモ"))
guest_name = config["member"].get("guest_name", "ゲスト")
database_file = config["database"].get("database_file", "mahjong.db")
channel_limitations = config["database"].get("channel_limitations", "")
commandword.update(check = config["database"].get("commandword", "麻雀成績チェック"))
commandword.update(help = config["help"].get("commandword", "ヘルプ"))

### 固定値 ###
opt = command_option()
prm = parameters()

wind = ("東家", "南家", "西家", "北家")
member_list = {}
team_list = {}

app_var = { # ホームタブ用
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours = -12)).strftime("%Y-%m-%d"),
}

logging.trace(f"{commandword=}") # type: ignore
logging.info(f"{slash_command=}")
logging.info(f"{ignore_userid=}")
logging.info(f"{channel_limitations=}")

# 作業用ディレクトリ作成
work_dir = os.path.join(os.path.realpath(os.path.curdir), work_dir)
if not os.path.isdir(work_dir):
    try:
        os.mkdir(work_dir)
    except:
        logging.error("Working directory creation failed !!!")
        sys.exit()

### slack api ###
try:
    app = App(token = os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token = os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit()
