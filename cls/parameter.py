import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

import global_value as g
from lib import command as c
from lib import function as f


class command_option:
    def __init__(self) -> None:
        self.initialization("DEFAULT")

    def initialization(self, _command: str, _argument: list = []) -> None:
        self.__dict__.clear()
        if _command not in g.cfg.config.sections():
            _command = "DEFAULT"

        self.command: str = _command
        self.aggregation_range: list = []
        self.target_player: list = []
        self.all_player: bool = False
        self.order: bool = False  # 順位推移グラフ / 成績上位者
        self.fourfold: bool = False  # 縦持ちデータの直近Nを4倍で取るか
        self.stipulated: int = 0  # 規定打数
        self.target_count: int = 0  # 直近
        self.interval: int = 80  # 区切りゲーム数
        self.verbose: bool = False  # 戦績詳細
        self.rating: bool = False  # レーティング表示

        self.aggregation_range.append(g.cfg.config[_command].get("aggregation_range", "当日"))
        self.individual: bool = g.cfg.config[_command].getboolean("individual", True)  # True:個人集計 / False:チーム集計
        self.statistics: bool = g.cfg.config[_command].getboolean("statistics", False)  # 統計
        self.unregistered_replace: bool = g.cfg.config[_command].getboolean("unregistered_replace", True)  # ゲスト無効
        self.guest_skip: bool = g.cfg.config[_command].getboolean("guest_skip", True)
        self.guest_skip2: bool = g.cfg.config[_command].getboolean("guest_skip2", True)
        self.score_comparisons: bool = g.cfg.config[_command].getboolean("score_comparisons", False)  # 比較
        self.game_results: bool = g.cfg.config[_command].getboolean("game_results", False)  # 戦績
        self.versus_matrix: bool = g.cfg.config[_command].getboolean("versus_matrix", False)
        self.ranked: int = g.cfg.config[_command].getint("ranked", 3)
        self.stipulated_rate: float = g.cfg.config[_command].getfloat("stipulated_rate", 0.05)
        self.filename: str = str()
        self.collection: str = str()

        self.format: str = g.cfg.config["setting"].get("format", "default")
        self.friendly_fire: bool = g.cfg.config["team"].getboolean("friendly_fire", True)
        self.group_length: int = g.cfg.config["comment"].getint("group_length", 0)
        self.search_word: str = g.cfg.config["comment"].get("search_word", str())

        # その他フラグ
        self.dbtools: bool = True  # dbtools実行時にTrue

        # 検索範囲の初期設定
        self.search_first: datetime = datetime.now()
        self.search_last: datetime = datetime.now()
        self.search_onday: datetime = datetime.now()
        self.set_search_range(self.aggregation_range)

        if _argument:
            self.update(_argument)

    def set_search_range(self, _argument: list) -> list:
        _target_days, _new_argument = f.common.scope_coverage(_argument)
        if _target_days:
            _first = min(_target_days)
            _onday = max(_target_days)
            _last = max(_target_days) + relativedelta(days=1)
            self.search_first = _first.replace(hour=12, minute=0, second=0, microsecond=0)
            self.search_last = _last.replace(hour=11, minute=59, second=59, microsecond=999999)
            self.search_onday = _onday.replace(hour=23, minute=59, second=59, microsecond=999999)

        return (_new_argument)

    def update(self, _argument: list) -> None:
        unknown_command = []

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
                case keyword if re.search(r"^(レート|レーティング|rate|ratings?)$", keyword):
                    self.rating = True
                case keyword if re.search(r"^(個人|個人成績)$", keyword):
                    self.individual = True
                case keyword if re.search(r"^(チーム|チーム成績|team)$", keyword.lower()):
                    self.individual = False
                case keyword if re.search(r"^(直近)([0-9]+)$", keyword):
                    self.target_count = int(re.sub(r"^(直近)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(トップ|上位|top)([0-9]+)$", keyword):
                    self.ranked = int(re.sub(r"^(トップ|上位|top)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(規定数|規定打数)([0-9]+)$", keyword):
                    self.stipulated = int(re.sub(r"^(規定数|規定打数)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(区間|区切り?|interval)([0-9]+)$", keyword):
                    self.interval = int(re.sub(r"^(区間|区切り?|interval)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(チーム同卓あり|コンビあり|同士討ち)$", keyword):
                    self.friendly_fire = True
                case keyword if re.search(r"^(チーム同卓なし|コンビなし)$", keyword):
                    self.friendly_fire = False
                case keyword if re.search(r"^(コメント|comment)(.+)$", keyword):
                    self.search_word = re.sub(r"^(コメント|comment)(.+)$", r"\2", keyword)
                case keyword if re.search(r"^(daily|デイリー|日次)$", keyword):
                    self.collection = "daily"
                case keyword if re.search(r"^(monthly|マンスリー|月次)$", keyword):
                    self.collection = "monthly"
                case keyword if re.search(r"^(yearly|イヤーリー|年次)$", keyword):
                    self.collection = "yearly"
                case keyword if re.search(r"^(全体)$", keyword):
                    self.collection = "all"
                case keyword if re.search(r"^(集約)([0-9]+)$", keyword):
                    self.group_length = int(re.sub(r"^(集約)([0-9]+)$", r"\2", keyword))
                case keyword if re.search(r"^(csv|text|txt)$", keyword.lower()):
                    self.format = keyword.lower()
                case keyword if re.search(r"^(filename:|ファイル名)(.+)$", keyword):
                    self.filename = re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword)
                case _:
                    unknown_command.append(keyword)

        # どのオプションにも該当しないキーワードはプレイヤー名 or チーム名
        if "target_player" in self.__dict__:
            for x in unknown_command:
                if x in [team["team"] for team in g.team_list]:
                    self.target_player.append(x)
                elif self.individual:
                    self.target_player.append(c.member.name_replace(x))
                else:
                    self.target_player.append(x)

    def check(self, _argument: list = []) -> None:
        self.__dict__.clear()
        self.update(_argument)


class parameters:
    def __init__(self) -> None:
        self.initialization()

    def initialization(self):
        self.__dict__.clear()
        self.rule_version: str = g.cfg.config["mahjong"].get("rule_version", "")
        self.origin_point: int = g.cfg.config["mahjong"].getint("point", 250)  # 配給原点
        self.return_point: int = g.cfg.config["mahjong"].getint("return", 300)  # 返し点
        self.player_name: str = str()
        self.guest_name: str = g.cfg.config["member"].get("guest_name", "ゲスト")
        self.search_word: str = str()
        self.player_list: dict = {}
        self.competition_list: dict = {}
        self.starttime = None
        self.starttime_hm = None
        self.starttime_hms = None
        self.starttime_y = None
        self.starttime_ym = None
        self.starttime_ymd = None
        self.endtime = None
        self.endtime_hm = None
        self.endtime_hms = None
        self.endtime_y = None
        self.endtime_ym = None
        self.endtime_ymd = None
        self.endonday_y = None
        self.endonday_ym = None
        self.endonday_ymd = None
        self.stipulated: int = 0
        self.target_count: int = 0

    def update(self, _opt: command_option):
        self.initialization()
        self.starttime = _opt.search_first  # 検索開始日
        self.starttime_hm = _opt.search_first.strftime("%Y/%m/%d %H:%M")
        self.starttime_hms = _opt.search_first.strftime("%Y/%m/%d %H:%M:%S")
        self.starttime_y = _opt.search_first.strftime("%Y")
        self.starttime_ym = _opt.search_first.strftime("%Y/%m")
        self.starttime_ymd = _opt.search_first.strftime("%Y/%m/%d")
        self.endtime = _opt.search_last  # 検索終了日
        self.endtime_hm = _opt.search_last.strftime("%Y/%m/%d %H:%M")
        self.endtime_hms = _opt.search_last.strftime("%Y/%m/%d %H:%M:%S")
        self.endtime_y = _opt.search_last.strftime("%Y")
        self.endtime_ym = _opt.search_last.strftime("%Y/%m")
        self.endtime_ymd = _opt.search_last.strftime("%Y/%m/%d")
        self.endonday_y = _opt.search_onday.strftime("%Y")
        self.endonday_ym = _opt.search_onday.strftime("%Y/%m")
        self.endonday_ymd = _opt.search_onday.strftime("%Y/%m/%d")
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
                    tmp_list = list(set(g.member_list))
                else:
                    tmp_list = _opt.target_player[1:]

                tmp_list2 = []
                for name in tmp_list:  # 名前ブレ修正
                    tmp_list2.append(c.member.name_replace(name, add_mark=False))
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
