import logging
import math
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

import lib.global_value as g
from lib import command as c
from lib import function as f


class CommandOption:
    """オプション解析クラス
    """

    def __init__(self) -> None:
        self.initialization("DEFAULT")

    def initialization(self, _command: str, _argument: list | None = None) -> None:
        """初期化処理

        Args:
            _command (str): 設定ファイルから読み込むセクション名
            _argument (list, optional): 引数リスト. Defaults to None.
        """

        self.__dict__.clear()
        if _command not in g.cfg.config.sections():
            _command = "DEFAULT"

        self.command: str = _command
        self.rule_version: str = str()
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
        self.anonymous: bool = False  # プレイヤー名を伏せる

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

        # 検索範囲の初期設定
        self.search_first: datetime = datetime.now()
        self.search_last: datetime = datetime.now()
        self.search_onday: datetime = datetime.now()
        self.set_search_range(self.aggregation_range)

        # 引数の処理
        self.always_argument: list = g.cfg.config[_command].get("always_argument", "").split()

        logging.info("Defaults: %s, argument: %s", self.__dict__, _argument)
        if self.always_argument:
            self.update(self.always_argument)

        logging.info("Always: %s, argument: %s", self.__dict__, _argument)
        if _argument:
            self.update(_argument)

        logging.info("Finally: %s, argument: %s", self.__dict__, _argument)

    def set_search_range(self, _argument: list) -> list:
        """検索範囲の日付をインスタンス変数にセットする

        Args:
            _argument (list): 引数リスト

        Returns:
            list: 引数リストから日付を取り除いたリスト
        """

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
        """引数を解析しインスタンス変数をセットする

        Args:
            _argument (list): 引数リスト
        """

        # 検索範囲取得
        _new_argument = self.set_search_range(_argument)

        # コマンドオプションフラグ変更
        unknown_command = []
        for keyword in _new_argument:
            check_word = f.common.hira_to_kana(keyword.lower())  # カタカナ、小文字に統一
            check_word = check_word.replace("無シ", "ナシ").replace("有リ", "アリ")  # 表記統一
            match check_word:
                case check_word if re.search(r"^ゲストナシ$", check_word):
                    self.guest_skip = False
                    self.guest_skip2 = False
                    self.unregistered_replace = True
                case check_word if re.search(r"^ゲストアリ$", check_word):
                    self.guest_skip = True
                    self.guest_skip2 = True
                    self.unregistered_replace = True
                case check_word if re.search(r"^ゲスト無効$", check_word):
                    self.unregistered_replace = False
                case check_word if re.search(r"^(全員|all)$", check_word):
                    self.all_player = True
                case check_word if re.search(r"^(比較|点差|差分)$", check_word):
                    self.score_comparisons = True
                case check_word if re.search(r"^(戦績)$", check_word):
                    self.game_results = True
                case check_word if re.search(r"^(対戦|対戦結果)$", check_word):
                    self.versus_matrix = True
                case check_word if re.search(r"^(詳細|verbose)$", check_word):
                    self.verbose = True
                case check_word if re.search(r"^(順位)$", check_word):
                    self.order = True
                case check_word if re.search(r"^(統計)$", check_word):
                    self.statistics = True
                case check_word if re.search(r"^(レート|レーティング|rate|ratings?)$", check_word):
                    self.rating = True
                case check_word if re.search(r"^(個人|個人成績)$", check_word):
                    self.individual = True
                case check_word if re.search(r"^(チーム|チーム成績|team)$", check_word):
                    self.individual = False
                case check_word if re.search(r"^(直近)([0-9]+)$", check_word):
                    self.target_count = int(re.sub(r"^(直近)([0-9]+)$", r"\2", check_word))
                case check_word if re.search(r"^(トップ|上位|top)([0-9]+)$", check_word):
                    self.ranked = int(re.sub(r"^(トップ|上位|top)([0-9]+)$", r"\2", check_word))
                case check_word if re.search(r"^(規定数|規定打数)([0-9]+)$", check_word):
                    self.stipulated = int(re.sub(r"^(規定数|規定打数)([0-9]+)$", r"\2", check_word))
                case check_word if re.search(r"^(区間|区切リ?|interval)([0-9]+)$", check_word):
                    self.interval = int(re.sub(r"^(区間|区切リ?|interval)([0-9]+)$", r"\2", check_word))
                case check_word if re.search(r"^(チーム同卓アリ|コンビアリ|同士討チ)$", check_word):
                    self.friendly_fire = True
                case check_word if re.search(r"^(チーム同卓ナシ|コンビナシ)$", check_word):
                    self.friendly_fire = False
                case check_word if re.search(r"^(コメント|comment)(.+)$", check_word):
                    self.search_word = re.sub(r"^(コメント|comment)(.+)$", r"\2", check_word)
                case check_word if re.search(r"^(daily|デイリー|日次)$", check_word):
                    self.collection = "daily"
                case check_word if re.search(r"^(monthly|マンスリー|月次)$", check_word):
                    self.collection = "monthly"
                case check_word if re.search(r"^(yearly|イヤーリー|年次)$", check_word):
                    self.collection = "yearly"
                case check_word if re.search(r"^(全体)$", check_word):
                    self.collection = "all"
                case check_word if re.search(r"^(集約)([0-9]+)$", check_word):
                    self.group_length = int(re.sub(r"^(集約)([0-9]+)$", r"\2", check_word))
                case check_word if re.search(r"^(ルール|rule)(.+)$", check_word):
                    self.rule_version = re.sub(r"^(ルール|rule)(.+)$", r"\2", keyword)
                case check_word if re.search(r"^(csv|text|txt)$", check_word):
                    self.format = check_word
                case check_word if re.search(r"^(filename:|ファイル名)(.+)$", check_word):
                    self.filename = re.sub(r"^(filename:|ファイル名)(.+)$", r"\2", keyword)
                case check_word if re.search(r"^(匿名|anonymous)$", check_word):
                    self.anonymous = True
                case _:
                    unknown_command.append(keyword)

        # どのオプションにも該当しないキーワードはプレイヤー名 or チーム名
        if "target_player" in self.__dict__:
            for x in unknown_command:
                if x in [team["team"] for team in g.team_list]:
                    self.target_player.append(x)
                elif self.individual:
                    self.target_player.append(c.member.name_replace(x, mask=False))
                else:
                    self.target_player.append(x)

    def check(self, _argument: list) -> None:
        """無効なオプションを引数リストから除外する

        Args:
            _argument (list, optional): 引数リスト
        """

        self.__dict__.clear()
        self.update(_argument)


class Parameters:
    """パラメータ解析クラス
    """

    def __init__(self) -> None:
        self.initialization()

    def initialization(self):
        """初期化処理
        """

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

    def update(self, _opt: CommandOption):
        """コマンド解析クラスの内容からパラメータをセットする

        Args:
            _opt (CommandOption): コマンド解析インスタンス
        """

        self.initialization()
        self.rule_version = _opt.rule_version if _opt.rule_version else self.rule_version
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
        """インスタンス変数を追加/更新する

        Args:
            _add_dict (dict): 追加する内容
        """

        self.__dict__.update(_add_dict)

    def get(self, x: str):
        return (self.__dict__.get(x, None))

    def stipulated_update(self, _opt: CommandOption, game_count: int):
        """規定打数計算

        Args:
            _opt (CommandOption): オプションパラメータ
            game_count (int): ゲーム数
        """

        if _opt.stipulated:
            self.stipulated = _opt.stipulated
        else:  # レートから計算
            self.stipulated = (
                math.ceil(game_count * _opt.stipulated_rate) + 1
            )

    def to_dict(self):
        """インスタンス変数を辞書で返す

        Returns:
            dict: インスタンス変数
        """

        tmp_dict = self.__dict__
        if self.player_list:
            tmp_dict.update(self.player_list)
        if self.competition_list:
            tmp_dict.update(self.competition_list)

        return (tmp_dict)
