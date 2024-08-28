import argparse
import configparser
import logging
import os
import re
import sys
from datetime import datetime
from functools import partial

import pandas as pd
from dateutil.relativedelta import relativedelta
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import lib.command as c


class command_option:
    def __init__(self) -> None:
        self.initialization("DEFAULT")

    def initialization(self, _command: str, _argument: list = []) -> None:
        self.__dict__.clear()
        if _command not in config.sections():
            _command = "DEFAULT"

        self.command: str = _command
        self.aggregation_range: list = []
        self.aggregation_range.append(config[_command].get("aggregation_range", "当日"))
        self.target_player: list = []
        self.all_player: bool = False
        self.order: bool = False  # 順位推移グラフ
        self.statistics: bool = False  # 統計レポート
        self.personal: bool = False  # 個人成績レポート
        self.fourfold: bool = False  # 縦持ちデータの直近Nを4倍で取るか
        self.stipulated: int = 0  # 規定打数
        self.target_count: int = 0  # 直近
        self.verbose: bool = False  # 戦績詳細
        self.team_total: bool = False  # チーム集計
        self.friendly_fire: bool = config["team"].getboolean("friendly_fire", True)
        self.unregistered_replace: bool = config[_command].getboolean("unregistered_replace", True)
        self.guest_skip: bool = config[_command].getboolean("guest_skip", True)
        self.guest_skip2: bool = config[_command].getboolean("guest_skip2", True)
        self.score_comparisons: bool = config[_command].getboolean("score_comparisons", False)
        self.game_results: bool = config[_command].getboolean("game_results", False)
        self.versus_matrix: bool = config[_command].getboolean("versus_matrix", False)
        self.ranked: int = config[_command].getint("ranked", 3)
        self.stipulated_rate: float = config[_command].getfloat("stipulated_rate", 0.05)
        self.format: str = config["setting"].get("format", "default")
        self.filename: str = str()
        self.daily: bool = False
        self.group_length: int = config["comment"].getint("group_length", 0)
        self.search_word: str = config["comment"].get("search_word", str())

        # 検索範囲の初期設定
        self.search_first: datetime = datetime.now()
        self.search_last: datetime = datetime.now()
        self.set_search_range(self.aggregation_range)

        if _argument:
            self.update(_argument)

    def set_search_range(self, _argument: list) -> list:
        _target_days, _new_argument = scope_coverage(_argument)
        if _target_days:
            _first = min(_target_days)
            _last = max(_target_days) + relativedelta(days=1)
            self.search_first = _first.replace(hour=12, minute=0, second=0, microsecond=0)
            self.search_last = _last.replace(hour=11, minute=59, second=59, microsecond=999999)

        return (_new_argument)

    def update(self, _argument: list) -> None:
        unkown_command = []

        # 検索範囲取得
        _new_argument = self.set_search_range(_argument)

        # コマンドオプションフラグ変更
        for keyword in _new_argument:
            match keyword.lower():
                case keyword if re.search(r"^ゲスト(なし|ナシ|無し)$", keyword):
                    self.guest_skip = False
                    self.guest_skip2 = False
                case keyword if re.search(r"^ゲスト(あり|アリ)$", keyword):
                    self.guest_skip = True
                    self.guest_skip2 = True
                case keyword if re.search(r"^ゲスト無効$", keyword):
                    self.unregistered_replace = False
                case keyword if re.search(r"^(全員|all)$", keyword):
                    self.all_player = True
                case keyword if re.search(r"^(比較|点差|差分)$", keyword):
                    self.score_comparisons = True
                case keyword if re.search(r"^(戦績)$", keyword):
                    self.game_results = True
                case keyword if re.search(r"^(対戦|対戦結果)$", keyword):
                    self.versus_matrix = True
                case keyword if re.search(r"^(詳細|verbose)$", keyword):
                    self.verbose = True
                case keyword if re.search(r"^(順位)$", keyword):
                    self.order = True
                case keyword if re.search(r"^(統計)$", keyword):
                    self.statistics = True
                case keyword if re.search(r"^(個人|個人成績)$", keyword):
                    self.personal = True
                case keyword if re.search(r"^(直近)([0-9]+)$", keyword):
                    self.target_count = int(re.sub(r"^(直近)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(トップ|上位|top)([0-9]+)$", keyword):
                    self.ranked = int(re.sub(r"^(トップ|上位|top)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(規定数|規定打数)([0-9]+)$", keyword):
                    self.stipulated = int(re.sub(r"^(規定数|規定打数)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(チーム|team)$", keyword.lower()):
                    self.team_total = True
                case keyword if re.search(r"^(チーム同卓あり|コンビあり|同士討ち)$", keyword):
                    self.friendly_fire = True
                case keyword if re.search(r"^(チーム同卓なし|コンビなし)$", keyword):
                    self.friendly_fire = False
                case keyword if re.search(r"^(コメント|comment)(.+)$", keyword):
                    self.search_word = re.sub(r"^(コメント|comment)(.+)$", r"\2", keyword)
                case keyword if re.search(r"^(daily|デイリー|日次)$", keyword):
                    self.daily = True
                case keyword if re.search(r"^(集約)([0-9]+)$", keyword):
                    self.group_length = int(re.sub(r"^(集約)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(csv|text|txt)$", keyword.lower()):
                    self.format = keyword.lower()
                case keyword if re.search(r"^(filename:|ファイル名)(.+)$", keyword):
                    self.filename = re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword)
                case _:
                    unkown_command.append(keyword)

        # どのオプションにも該当しないキーワードはプレイヤー名
        if "target_player" in self.__dict__:
            for x in unkown_command:
                self.target_player.append(c.member.NameReplace(x))

    def check(self, _argument: list = []) -> None:
        self.__dict__.clear()
        self.update(_argument)


class parameters:
    def __init__(self) -> None:
        self.initialization()

    def initialization(self):
        self.__dict__.clear()
        self.rule_version: str = config["mahjong"].get("rule_version", "")
        self.origin_point: int = config["mahjong"].getint("point", 250)  # 配給原点
        self.return_point: int = config["mahjong"].getint("return", 300)  # 返し点
        self.player_name: str = str()
        self.guest_name: str = config["member"].get("guest_name", "ゲスト")
        self.search_word: str = str()
        self.player_list: dict = {}
        self.competition_list: dict = {}
        self.starttime = None
        self.starttime_hm = None
        self.starttime_hms = None
        self.endtime = None
        self.endtime_hm = None
        self.endtime_hms = None
        self.stipulated: int = 0
        self.target_count: int = 0

    def update(self, _opt: command_option):
        self.initialization()
        self.starttime = _opt.search_first  # 検索開始日
        self.endtime = _opt.search_last  # 検索終了日
        self.starttime_hm = _opt.search_first.strftime("%Y/%m/%d %H:%M")
        self.endtime_hm = _opt.search_last.strftime("%Y/%m/%d %H:%M")
        self.starttime_hms = _opt.search_first.strftime("%Y/%m/%d %H:%M:%S")
        self.endtime_hms = _opt.search_last.strftime("%Y/%m/%d %H:%M:%S")
        self.target_count = _opt.target_count
        self.stipulated = _opt.stipulated
        self.group_length = _opt.group_length

        if _opt.target_player:
            self.player_name = _opt.target_player[0]
            count = 0
            for name in list(set(_opt.target_player)):
                self.player_list[f"player_{count}"] = name
                count += 1

            # 複数指定
            if len(_opt.target_player) >= 1:
                count = 0
                if _opt.all_player:  # 全員対象
                    tmp_list = list(set(member_list))
                else:
                    tmp_list = _opt.target_player[1:]

                tmp_list2 = []
                for name in tmp_list:  # 名前ブレ修正
                    tmp_list2.append(c.member.NameReplace(name, add_mark=False))
                for name in list(set(tmp_list2)):  # 集計対象者の名前はリストに含めない
                    if name != self.player_name:
                        self.competition_list[f"competition_{count}"] = name
                        count += 1

        if _opt.search_word:
            self.search_word = f"%{_opt.search_word}%"

    def append(self, _add_dict: dict):
        self.__dict__.update(_add_dict)

    def to_dict(self):
        tmp_dict = self.__dict__
        if self.player_list:
            tmp_dict.update(self.player_list)
        if self.competition_list:
            tmp_dict.update(self.competition_list)

        return (tmp_dict)


class Message_Parser():
    client: WebClient = WebClient()
    channel_id: str = str()
    user_id: str = str()
    bot_id: str = str()
    text: str = str()
    event_ts: str = str()  # テキストのまま処理する
    thread_ts: str = str()  # テキストのまま処理する
    status: str = str()
    keyword: str = str()
    argument: list = list()
    updatable: bool = bool()
    checked: bool = bool()

    def __init__(self, body: dict = {}):
        if body is dict():
            self.parser(body)

    def parser(self, _body: dict):
        self.__dict__.clear()
        self.client = WebClient()
        self.text = str()
        self.thread_ts = str()
        self.checked = False
        _event = {}

        if "channel_name" in _body:
            if _body["channel_name"] == "directmessage":
                self.channel_id = _body["channel_id"]
                self.text = _body["text"]
                self.event_ts = "0"
        elif "container" in _body:
            self.channel_id = _body["user"]["id"]
        else:
            self.channel_id = _body["event"]["channel"]

            if _body["authorizations"][0]["is_bot"]:
                self.bot_id = _body["authorizations"][0]["user_id"]
            else:
                self.bot_id = str()

            if "subtype" in _body["event"]:
                match _body["event"]["subtype"]:
                    case "message_changed":
                        self.status = "message_changed"
                        _event = _body["event"]["message"]
                    case "message_deleted":
                        self.status = "message_deleted"
                        _event = _body["event"]["previous_message"]
                    case "file_share":
                        self.status = "message_append"
                        _event = _body["event"]
                    case _:
                        pass
            else:
                self.status = "message_append"
                _event = _body["event"]

            for x in _event:
                match x:
                    case "user":
                        self.user_id = _event["user"]
                    case "ts":
                        self.event_ts = _event["ts"]
                    case "thread_ts":
                        self.thread_ts = _event["thread_ts"]
                    case "blocks":
                        if "text" in _event["blocks"][0]["elements"][0]["elements"][0]:
                            self.text = _event["blocks"][0]["elements"][0]["elements"][0]["text"]
                        else:  # todo: 解析用出力
                            logging.info(f"<analysis> blocks in: {_event=}")

        if self.text:
            self.keyword = self.text.split()[0]
            self.argument = self.text.split()[1:]  # 最初のスペース以降はコマンド引数扱い

        # DB更新可能チャンネルのポストかチェック
        if not len(channel_limitations) or self.channel_id in channel_limitations.split(","):
            self.updatable = True
        else:
            self.updatable = False

    def parser_dm(self, _body: dict):
        self.__dict__.clear()
        self.client = WebClient()
        self.channel_id = _body["channel_id"]
        self.text = _body["text"]
        self.event_ts = "0"
        self.thread_ts = str()
        self.checked = False

        if self.text:
            self.keyword = self.text.split()[0]
            self.argument = self.text.split()[1:]  # 最初のスペース以降はコマンド引数扱い


def scope_coverage(argument: list):
    """
    キーワードから有効な日付を取得する

    Parameters
    ----------
    argument : list
        チェック対象のキーワードリスト

    Returns
    -------
    new_argument : list
        日付を得られなっかったキーワードのリスト

    target_days : list
        キーワードから得た日付のリスト
    """

    new_argument = argument.copy()
    target_days = []
    current_time = datetime.now()
    appointed_time = current_time + relativedelta(hours=-12)

    for x in argument:
        match x:
            case x if re.match(r"^([0-9]{8}|[0-9/.-]{8,10})$", x):
                try_day = pd.to_datetime(x, errors="coerce").to_pydatetime()
                target_days.append(try_day)
                new_argument.remove(x)
            case "当日":
                target_days.append(appointed_time)
                new_argument.remove(x)
            case "今日":
                target_days.append(current_time)
                new_argument.remove(x)
            case "昨日":
                target_days.append((current_time + relativedelta(days=-1)))
                new_argument.remove(x)
            case "今月":
                target_days.append((appointed_time + relativedelta(day=1, months=0)))
                target_days.append((appointed_time + relativedelta(day=1, months=1, days=-1,)))
                new_argument.remove(x)
            case "先月":
                target_days.append((appointed_time + relativedelta(day=1, months=-1)))
                target_days.append((appointed_time + relativedelta(day=1, months=0, days=-1,)))
                new_argument.remove(x)
            case "先々月":
                target_days.append((appointed_time + relativedelta(day=1, months=-2)))
                target_days.append((appointed_time + relativedelta(day=1, months=-1, days=-1,)))
                new_argument.remove(x)
            case "今年":
                target_days.append((current_time + relativedelta(day=1, month=1)))
                target_days.append((current_time + relativedelta(day=31, month=12)))
                new_argument.remove(x)
            case "去年" | "昨年":
                target_days.append((current_time + relativedelta(day=1, month=1, years=-1)))
                target_days.append((current_time + relativedelta(day=31, month=12, years=-1)))
                new_argument.remove(x)
            case "一昨年":
                target_days.append((current_time + relativedelta(day=1, month=1, years=-2)))
                target_days.append((current_time + relativedelta(day=31, month=12, years=-2)))
                new_argument.remove(x)
            case "最後":
                target_days.append((current_time + relativedelta(days=1)))
                new_argument.remove(x)
            case "全部":
                target_days.append((current_time + relativedelta(years=-10)))
                target_days.append((current_time + relativedelta(days=1)))
                new_argument.remove(x)

    return (target_days, new_argument)


def parser():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=True,
    )

    p.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ情報表示",
    )

    p.add_argument(
        "--verbose",
        action="store_true",
        help="詳細デバッグ情報表示",
    )

    p.add_argument(
        "--moderate",
        action="store_true",
        help="ログレベルがエラー以下のもを非表示",
    )

    p.add_argument(
        "--notime",
        action="store_true",
        help="ログフォーマットから日時を削除",
    )

    p.add_argument(
        "-c", "--config",
        default="config.ini",
        metavar="config.ini",
        help="設定ファイル",
    )

    # 動作テスト用オプション(非表示)
    p.add_argument(
        "-t", "--testcase",
        help=argparse.SUPPRESS,
    )

    p.add_argument(
        "--classic",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    p.add_argument(
        "--profile",
        help=argparse.SUPPRESS,
    )

    return (p.parse_args())


# --- ログレベル追加
# TRACE
logging.TRACE = 19  # type: ignore
logging.trace = partial(logging.log, logging.TRACE)  # type: ignore
logging.addLevelName(logging.TRACE, "TRACE")  # type: ignore
# NOTICE
logging.NOTICE = 25  # type: ignore
logging.notice = partial(logging.log, logging.NOTICE)  # type: ignore
logging.addLevelName(logging.NOTICE, "NOTICE")  # type: ignore

# --- コマンドラインオプション解析
args = parser()

if args.notime:
    fmt = "[%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"
else:
    fmt = "[%(asctime)s][%(levelname)s][%(name)s:%(module)s:%(funcName)s] %(message)s"

if args.debug:
    if args.verbose:
        print("DEBUG MODE(verbose)")
        logging.basicConfig(level=logging.TRACE, format=fmt)  # type: ignore
    else:
        print("DEBUG MODE")
        logging.basicConfig(level=logging.INFO, format=fmt)
else:
    if args.moderate:
        logging.basicConfig(level=logging.WARNING, format=fmt)
    else:
        logging.basicConfig(level=logging.NOTICE, format=fmt)  # type: ignore

# --- 設定ファイル読み込み
try:
    config = configparser.ConfigParser()
    config.read(args.config, encoding="utf-8")
    logging.notice(f"config read: {args.config} -> {config.sections()}")  # type: ignore
except Exception:
    sys.exit()

# 必須セクションチェック
for x in ("mahjong", "setting"):
    if x not in config.sections():
        sys.exit()

# オプションセクションチェック
for x in ("results", "graph", "ranking", "report", "member", "team", "database", "comment", "help"):
    if x not in config.sections():
        config.add_section(x)

commandword = {  # チャンネル内呼び出しキーワード
    "help": config["help"].get("commandword", "ヘルプ"),
    "results": config["results"].get("commandword", "麻雀成績"),
    "graph": config["graph"].get("commandword", "麻雀グラフ"),
    "ranking": config["ranking"].get("commandword", "麻雀ランキング"),
    "report": config["report"].get("commandword", "麻雀成績レポート"),
    "member": config["member"].get("commandword", "メンバー一覧"),
    "team": config["team"].get("commandword", "チーム一覧"),
    "remarks_word": config["setting"].get("remarks_word", "麻雀成績メモ"),
    "check": config["database"].get("commandword", "麻雀成績チェック"),
}

slash_command = config["setting"].get("slash_commandname", "/mahjong")
guest_mark = config["setting"].get("guest_mark", "※")
reaction_ok = config["setting"].get("reaction_ok", "ok")
reaction_ng = config["setting"].get("reaction_ng", "ng")
font_file = config["setting"].get("font_file", "ipaexg.ttf")
work_dir = config["setting"].get("work_dir", "work")
ignore_userid = [x.strip() for x in config["setting"].get("ignore_userid", "").split(",")]
database_file = config["database"].get("database_file", "mahjong.db")
channel_limitations = config["database"].get("channel_limitations", "")

# 固定値
opt = command_option()
prm = parameters()
msg = Message_Parser()

wind = ("東家", "南家", "西家", "北家")
member_list = {}
team_list = {}

app_var = {  # ホームタブ用
    "user_id": None,
    "view_id": None,
    "screen": None,
    "sday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
    "eday": (datetime.now() + relativedelta(hours=-12)).strftime("%Y-%m-%d"),
}

logging.trace(f"{commandword=}")  # type: ignore
logging.info(f"{slash_command=}")
logging.info(f"{ignore_userid=}")
logging.info(f"{channel_limitations=}")

# 作業用ディレクトリ作成
work_dir = os.path.join(os.path.realpath(os.path.curdir), work_dir)
if not os.path.isdir(work_dir):
    try:
        os.mkdir(work_dir)
    except Exception:
        logging.error("Working directory creation failed !!!")
        sys.exit()

# --- slack api
try:
    app = App(token=os.environ["SLACK_BOT_TOKEN"])
    webclient = WebClient(token=os.environ["SLACK_WEB_TOKEN"])
except SlackApiError as e:
    logging.error(e)
    sys.exit()
