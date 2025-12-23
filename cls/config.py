"""
cls/config.py
"""

import logging
import shutil
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from itertools import chain
from math import ceil
from pathlib import Path, PosixPath
from types import NoneType
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeAlias, Union

from libs.types import GradeTableDict

if TYPE_CHECKING:
    from configparser import SectionProxy

    from libs.types import MemberDataDict, TeamDataDict

SubClassType: TypeAlias = Union[
    "MahjongSection",
    "SettingSection",
    "MemberSection",
    "TeamSection",
    "AliasSection",
    "DropItems",
    "BadgeDisplay",
    "SubCommand",
    "KeywordMapping",
]


class CommonMethodMixin:
    """共通メソッド"""

    _section: "SectionProxy"

    def get(self, key: str, fallback: Any = None) -> Any:
        """値の取得"""
        return self._section.get(key, fallback)

    def getint(self, key: str, fallback: int = 0) -> int:
        """整数値の取得"""
        return self._section.getint(key, fallback)

    def getfloat(self, key: str, fallback: float = 0.0) -> float:
        """数値の取得"""
        return self._section.getfloat(key, fallback)

    def getboolean(self, key: str, fallback: bool = False) -> bool:
        """真偽値の取得"""
        return self._section.getboolean(key, fallback)

    def getlist(self, key: str) -> list:
        """リストの取得"""
        return [x.strip() for x in self._section.get(key, "").split(",")]

    def keys(self) -> list:
        """キーリストの返却"""
        return list(self._section.keys())

    def values(self) -> list:
        """値リストの返却"""
        return list(self._section.values())

    def items(self):
        """ItemsViewを返却"""
        return self._section.items()

    def to_dict(self) -> dict[str, str]:
        """辞書型に変換"""
        return dict(self._section.items())


class BaseSection(CommonMethodMixin):
    """共通処理"""

    def __init__(self, outer: SubClassType, section_name: str):
        parser = outer._parser
        if section_name not in parser:
            return
        self._section = parser[section_name]

        self.initialization()
        self.section = section_name  # セクション名保持

    def __repr__(self) -> str:
        return str({k: v for k, v in vars(self).items() if not str(k).startswith("_")})

    def initialization(self):
        """設定ファイルから値の取り込み"""
        for k in self._section.keys():
            match type(self.__dict__.get(k)):
                case v_type if k in self.__dict__ and v_type is str:
                    setattr(self, k, self._section.get(k, fallback=self.get(k)))
                case v_type if k in self.__dict__ and v_type is int:
                    setattr(self, k, self._section.getint(k, fallback=self.get(k)))
                case v_type if k in self.__dict__ and v_type is float:
                    setattr(self, k, self._section.getfloat(k, fallback=self.get(k)))
                case v_type if v_type is bool:
                    setattr(self, k, self._section.getboolean(k, fallback=self.get(k)))
                case v_type if k in self.__dict__ and v_type is list:
                    v_list = [x.strip() for x in self._section.get(k, fallback=self.get(k)).split(",")]
                    current_list = getattr(self, k)
                    if isinstance(current_list, list) and current_list:  # 設定済みリストは追加
                        current_list.extend(v_list)
                    else:
                        setattr(self, k, v_list)
                case v_type if k in self.__dict__ and v_type is Optional[str]:  # 文字列 or None(未定義)
                    setattr(self, k, self._section.get(k, fallback=self.get(k)))
                case v_type if k in self.__dict__ and v_type is PosixPath:
                    setattr(self, k, Path(self._section.get(k, fallback=self.get(k))))
                case v_type if k in self.__dict__ and v_type is NoneType:
                    if k in ["backup_dir"]:  # ディレクトリを指定する設定はPathで格納
                        setattr(self, k, Path(self._section.get(k, fallback=self.get(k))))
                    else:
                        setattr(self, k, self._section.get(k, fallback=self.get(k)))
                case _:
                    setattr(self, k, self.__dict__.get(k))

    def to_dict(self) -> dict:
        """必要なパラメータを辞書型で返す

        Returns:
            dict: 返却値
        """

        ret_dict: dict = {}
        for key in vars(self):
            if key.startswith("_"):
                continue
            ret_dict[key] = getattr(self, key)

        return ret_dict


class MahjongSection(BaseSection):
    """mahjongセクション処理"""

    mode: Literal[3, 4]
    """ 集計モード切替(四人打ち/三人打ち)"""
    rule_version: str
    """ルール判別識別子"""
    origin_point: int
    """配給原点"""
    return_point: int
    """返し点"""
    rank_point: list
    """順位点"""
    ignore_flying: bool
    """トビカウント
    - *True*: なし
    - *False*: あり
    """
    draw_split: bool
    """同点時の順位点
    - *True*: 山分けにする
    - *False*: 席順で決める
    """
    regulations_type2: list
    """メモで役満として扱う単語リスト(カンマ区切り)"""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.mode = int(4)
        self.rule_version = str("")
        self.origin_point = int(250)
        self.return_point = int(300)
        self.rank_point: list = [30, 10, -10, -30]
        self.ignore_flying = bool(False)
        self.draw_split = bool(False)
        self.regulations_type2 = []

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "mahjong"
        self._parser = outer._parser
        self._reset()
        super().__init__(self, _section_name)

        # 順位点更新
        if not self.rank_point:
            self.rank_point = [30, 10, -10, -30]
        self.rank_point = list(map(int, self.rank_point[:4]))  # 数値化

        logging.debug("%s: %s", _section_name, self)


class SettingSection(BaseSection):
    """settingセクション処理"""

    help: str
    """ヘルプ表示キーワード"""
    keyword: str
    """成績記録キーワード(プライマリ)"""
    remarks_word: str
    """メモ記録用キーワード"""
    time_adjust: int
    """日付変更後、集計範囲に含める追加時間"""
    separate: bool
    """スコア入力元識別子別集計フラグ
    - *True*: 識別子別に集計
    - *False*: すべて集計
    """
    search_word: str
    """コメント固定(検索時の検索文字列)"""
    group_length: int
    """コメント固定(検索時の集約文字数)"""
    guest_mark: str
    """ゲスト無効時に未登録メンバーに付与する印"""
    database_file: Union[str, Path]
    """成績管理データベースファイル名"""
    backup_dir: Optional[Path]
    """バックアップ先ディレクトリ"""
    font_file: Path
    """グラフ描写に使用するフォントファイル"""
    graph_style: str
    """グラフスタイル"""
    work_dir: Path

    def __init__(self):
        self._reset()

    def _reset(self):
        self.help = str("麻雀成績ヘルプ")
        self.keyword = str("終局")
        self.remarks_word = str("麻雀成績メモ")
        self.time_adjust = int(12)
        self.separate = bool(False)
        self.search_word = str("")
        self.group_length = int(0)
        self.guest_mark = str("※")
        self.database_file = Path("mahjong.db")
        self.backup_dir = None
        self.font_file = Path("ipaexg.ttf")
        self.graph_style = str("ggplot")
        self.work_dir = Path("work")

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "setting"
        self._parser = outer._parser
        self._reset()
        super().__init__(self, _section_name)

        # 作業用ディレクトリ作成
        if self.work_dir.is_dir():
            shutil.rmtree(self.work_dir)
        try:
            self.work_dir.mkdir(exist_ok=True)
        except FileExistsError as err:
            sys.exit(str(err))

        # フォントファイルチェック
        for chk_dir in (outer.config_dir, outer.script_dir):
            chk_file = chk_dir / str(self.font_file)
            if chk_file.exists():
                self.font_file = chk_file
                break
        else:
            if not self.font_file.exists():
                logging.critical("The specified font file cannot be found.")
                sys.exit(255)

        # データベース関連
        if isinstance(self.database_file, Path) and not self.database_file.exists():
            self.database_file = outer.config_dir / str(self.database_file)

        if isinstance(self.backup_dir, PosixPath):
            try:
                self.backup_dir.mkdir(exist_ok=True)
            except FileExistsError as err:
                sys.exit(str(err))

        logging.debug("%s: %s", _section_name, self)


class MemberSection(BaseSection):
    """memberセクション処理"""

    info: list["MemberDataDict"]
    """メンバー情報"""
    registration_limit: int
    """登録メンバー上限数"""
    character_limit: int
    """名前に使用できる文字数"""
    alias_limit: int
    """別名登録上限数"""
    guest_name: str
    """未登録メンバー名称"""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.info = []
        self.registration_limit = int(255)
        self.character_limit = int(8)
        self.alias_limit = int(16)
        self.guest_name = str("ゲスト")

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "member"
        self._parser = outer._parser
        self._reset()
        super().__init__(self, _section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get(_section_name, "commandword", fallback="メンバー一覧").split(",")]

        logging.debug("%s: %s", _section_name, self)

    def alias(self, name: str) -> list[str]:
        """指定メンバーの別名をリストで返す

        Args:
            name (str): メンバー名

        Returns:
            list[str]: 別名リスト
        """

        for x in self.info:
            if x.get("name") == name:
                return x.get("alias")
        return []

    @property
    def lists(self) -> list[str]:
        """メンバー名一覧をリストで返す"""

        return [x.get("name") for x in self.info]

    @property
    def all_lists(self) -> list[str]:
        """メンバー名、別名をすべてリストで返す

        Returns:
            list[str]: _description_
        """

        ret: list[str] = []
        for name in self.lists:
            ret.append(name)
            ret.extend(self.alias(name))

        return list(set(ret))


class TeamSection(BaseSection):
    """teamセクション処理"""

    info: list["TeamDataDict"]
    """チーム情報"""
    registration_limit: int
    """登録チーム上限数"""
    character_limit: int
    """チーム名に使用できる文字数"""
    member_limit: int
    """チームに所属できるメンバー上限"""
    friendly_fire: bool
    """チームメイトが同卓しているゲームを集計対象に含めるか"""

    def __init__(self):
        self._reset()

    def _reset(self):
        self.info = []
        self.registration_limit = int(255)
        self.character_limit = int(16)
        self.member_limit = int(16)
        self.friendly_fire = bool(True)

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "team"
        self._parser = outer._parser
        self._reset()
        super().__init__(self, _section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get(_section_name, "commandword", fallback="チーム一覧").split(",")]

        logging.debug("%s: %s", _section_name, self)

    def member(self, team: str) -> list[str]:
        """チーム所属メンバーをリストで返す

        Args:
            team (str): チーム名

        Returns:
            list[str]: 所属メンバーリスト
        """

        for x in self.info:
            if x.get("team") == team:
                return x.get("member")
        return []

    def which(self, name: str) -> str | None:
        """指定メンバーの所属チームを返す

        Args:
            name (str): チェック対象のメンバー名

        Returns:
            Union[str, None]:
            - str: 所属しているチーム名
            - None: 未所属
        """

        for team in self.lists:
            if name in self.member(team):
                return team

        return None

    @property
    def lists(self) -> list[str]:
        """チーム名一覧をリストで返す"""

        return [x.get("team") for x in self.info]


class AliasSection(BaseSection):
    """aliasセクション処理"""

    results: list
    """成績サマリ出力コマンド"""
    graph: list
    """成績グラフ出力コマンド"""
    ranking: list
    """ランキング出力コマンド"""
    report: list
    """レポート出力コマンド"""
    download: list
    member: list
    """メンバーリスト表示コマンド"""
    add: list
    delete: list
    team_create: list
    team_del: list
    team_add: list
    team_remove: list
    team_list: list
    """チームリスト出力コマンド"""
    team_clear: list

    def __init__(self):
        self._reset()

    def _reset(self):
        self.results = ["results", "成績"]
        self.graph = ["graph", "グラフ"]
        self.ranking = ["ranking", "ランキング"]
        self.report = ["report", "レポート"]
        self.download = ["download", "ダウンロード"]
        self.member = ["member", "userlist", "member_list"]
        self.add = ["add"]
        self.delete = ["del"]
        self.team_create = ["team_create"]
        self.team_del = ["team_del"]
        self.team_add = ["team_add"]
        self.team_remove = ["team_remove"]
        self.team_list = ["team_list"]
        self.team_clear = ["team_clear"]

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "alias"
        self._parser = outer._parser
        self._reset()
        super().__init__(self, _section_name)

        # delのエイリアス取り込み(設定ファイルに`delete`と書かれていない)
        list_data = [x.strip() for x in str(self._parser.get("alias", "del", fallback="del")).split(",")]
        self.delete.extend(list_data)

        logging.debug("%s: %s", _section_name, self)


class DropItems(BaseSection):
    """非表示項目リスト"""

    def __init__(self, outer: "AppConfig"):
        self._parser = outer._parser

        # 設定値取り込み
        super().__init__(self, "")
        self.results: set = {x.strip() for x in self._parser.get("results", "dropitems", fallback="").split(",")}
        """成績サマリ非表示項目"""
        self.ranking: set = {x.strip() for x in self._parser.get("ranking", "dropitems", fallback="").split(",")}
        """ランキング/レーティング非表示項目"""
        self.report: set = {x.strip() for x in self._parser.get("report", "dropitems", fallback="").split(",")}
        """レポート非表示項目"""

        # 固定ワード
        self.flying = {"トビ", "トビ率"}
        """トビ関連データ非表示指定ワード"""
        self.yakuman = {"役満", "役満和了", "役満和了率"}
        """役満和了関連データ非表示指定ワード"""
        self.regulation = {"卓外", "卓外清算", "卓外ポイント"}
        """卓外清算関連データ非表示指定ワード"""
        self.other = {"その他", "メモ"}
        """メモ関連データ非表示指定ワード"""


class BadgeDisplay(BaseSection):
    """バッジ表示"""

    @dataclass
    class BadgeGradeSpec:
        """段位"""

        table_name: str = field(default=str())
        table: GradeTableDict = field(default_factory=GradeTableDict)

    grade: "BadgeGradeSpec" = BadgeGradeSpec()

    def __init__(self, outer: "AppConfig"):
        self._parser = outer._parser
        super().__init__(self, "")

        self.grade.table_name = self._parser.get("grade", "table_name", fallback="")


class SubCommand(BaseSection):
    """サブコマンドセクション処理"""

    section: str
    """サブコマンドセクション名"""

    commandword: list
    """呼び出しキーワード"""
    aggregation_range: str
    """検索範囲未指定時に使用される範囲"""
    individual: bool
    """個人/チーム集計切替フラグ
    - *True*: 個人集計
    - *False*: チーム集計
    """
    all_player: bool
    daily: bool
    fourfold: bool
    game_results: bool
    guest_skip: bool
    guest_skip2: bool
    ranked: int
    score_comparisons: bool
    """スコア比較"""
    statistics: bool
    """統計情報表示"""
    stipulated: int
    """規定打数指定"""
    stipulated_rate: float
    """規定打数計算レート"""
    unregistered_replace: bool
    """メンバー未登録プレイヤー名をゲストに置き換えるかフラグ
    - *True*: 置き換える
    - *False*: 置き換えない
    """
    anonymous: bool
    """匿名化フラグ"""
    verbose: bool
    """詳細情報出力フラグ"""
    versus_matrix: bool
    """対戦マトリックス表示"""
    collection: str
    always_argument: list
    """オプションとして常に付与される文字列"""
    format: str
    filename: str
    interval: int

    def __init__(self, section_name: str):
        self._reset(section_name)

    def _reset(self, section_name: str):
        self.section = section_name
        self.commandword = []
        self.aggregation_range = str("当日")
        self.individual = bool(True)
        self.all_player = bool(False)
        self.daily = bool(True)
        self.fourfold = bool(True)
        self.game_results = bool(False)
        self.guest_skip = bool(True)
        self.guest_skip2 = bool(True)
        self.ranked = int(3)
        self.score_comparisons = bool(False)
        self.statistics = bool(False)
        self.stipulated = int(0)
        self.stipulated_rate = 0.05
        self.unregistered_replace = bool(True)
        self.anonymous = bool(False)
        self.verbose = bool(False)
        self.versus_matrix = bool(False)
        self.collection = str("")
        self.always_argument = []
        self.format = str("")
        self.filename = str("")
        self.interval = 80

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        self._parser = outer._parser
        self._reset(self.section)
        super().__init__(self, self.section)

        # 呼び出しキーワード取り込み
        default_word = {
            "results": "麻雀成績",
            "graph": "麻雀グラフ",
            "ranking": "麻雀ランキング",
            "report": "麻雀成績レポート",
        }
        self.commandword = [x.strip() for x in self._parser.get(self.section, "commandword", fallback=default_word[self.section]).split(",")]

        logging.debug("%s: %s", self.section, self)

    def stipulated_calculation(self, game_count: int) -> int:
        """規定打数をゲーム数から計算

        Args:
            game_count (int): 指定ゲーム数

        Returns:
            int: 規定ゲーム数
        """

        return int(ceil(game_count * self.stipulated_rate) + 1)


class KeywordMapping(BaseSection):
    """secondary_keywordセクション処理"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser
        self.rule: dict[str, Path] = {}
        """追加キーワード"""

        # 設定値取り込み
        for k, v in self._parser.items(section_name):
            if (overwrite := Path(v)).exists():
                self.rule.update({f"{k}": overwrite})
            if v == "":
                self.rule.update({f"{k}": outer.config_file})


class AppConfig:
    """コンフィグ解析クラス"""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        try:
            self.main_parser = ConfigParser()
            self.main_parser.read(self.config_file, encoding="utf-8")
            self._parser = self.main_parser
        except Exception as err:
            raise RuntimeError(err) from err

        # 必須セクションチェック
        for x in ("mahjong", "setting"):
            if x not in self._parser.sections():
                logging.critical("Required section not found. (%s)", x)
                sys.exit(255)

        # オプションセクションチェック
        option_sections = [
            "results",
            "graph",
            "ranking",
            "report",
            "alias",
            "member",
            "team",
            "regulations",
            "regulations_them",
            "secondary_keyword",
        ]
        for x in option_sections:
            if x not in self._parser.sections():
                self._parser.add_section(x)

        # set base directory
        self.script_dir = Path(sys.argv[0]).absolute().parent
        """スクリプトが保存されているディレクトリパス"""
        self.config_dir = self.config_file.absolute().parent
        """設定ファイルが保存されているディレクトリパス"""

        # 設定値
        self.setting = SettingSection()
        """settingセクション設定値"""
        self.mahjong = MahjongSection()
        """mahjongセクション設定値"""
        self.alias = AliasSection()
        """aliasセクション設定値"""

        self.member = MemberSection()
        """memberセクション設定値"""
        self.team = TeamSection()
        """teamセクション設定値"""

        self.dropitems = DropItems(self)
        """非表示項目"""

        self.badge = BadgeDisplay(self)
        """バッジ設定"""

        # サブコマンド
        self.results = SubCommand("results")
        """resultsセクション設定値"""
        self.graph = SubCommand("graph")
        """graphセクション設定値"""
        self.ranking = SubCommand("ranking")
        """rankingセクション設定値"""
        self.report = SubCommand("report")
        """reportセクション設定値"""

        # 共通設定値
        self.undefined_word: int = 0
        """レギュレーションワードテーブルに登録されていないワードの種別"""
        self.aggregate_unit: Literal["A", "M", "Y", None] = None
        """レポート生成用日付範囲デフォルト値(レポート生成用)
        - *A*: 全期間
        - *M*: 月別
        - *Y*: 年別
        - *None*: 未定義
        """

        self.initialization()

        self.keyword = KeywordMapping(self, "secondary_keyword")
        """成績登録キーワード"""
        if self.setting.keyword not in self.keyword.rule:
            self.keyword.rule.update({self.setting.keyword: self.config_file})

    def initialization(self):
        """設定ファイル読み込み"""

        self._parser = self.main_parser

        self.setting.config_load(self)
        self.mahjong.config_load(self)
        self.alias.config_load(self)
        self.member.config_load(self)
        self.team.config_load(self)

        self.results.config_load(self)
        self.graph.config_load(self)
        self.ranking.config_load(self)
        self.report.config_load(self)

    def word_list(self) -> list:
        """設定されている値、キーワードをリスト化する

        Returns:
            list: リスト化されたキーワード
        """

        words: list = [
            [self.setting.remarks_word],
            self.results.commandword,
            self.graph.commandword,
            self.ranking.commandword,
            self.report.commandword,
        ]

        for k, v in self.alias.to_dict().items():
            if isinstance(v, list):
                words.append([k])
                words.append(v)

        for k in self.keyword.rule.keys():
            words.append([k])

        words = list(set(chain.from_iterable(words)))  # 重複排除/平滑化
        words = [x for x in words if x != ""]  # 空文字削除

        return words

    def overwrite(self, additional_config: Path, section_name: str):
        """指定セクションを上書き

        Args:
            additional_config (Path): 追加設定ファイルパス
            section_name (str): セクション名
        """

        if not additional_config.exists():
            return

        try:
            self._parser = ConfigParser()
            self._parser.read([self.config_file, additional_config], encoding="utf-8")
        except Exception as err:
            logging.error(err)
            return

        protected_values: Union[str, list]
        match section_name:
            case "setting":
                protected_values = self.setting.help  # 上書き保護
                self.setting.config_load(self)
                self.setting.help = protected_values
            case "mahjong":
                self.mahjong.config_load(self)
            case "results":
                protected_values = self.results.commandword  # 上書き保護
                self.results.config_load(self)
                self.results.commandword = protected_values
            case "graph":
                protected_values = self.graph.commandword  # 上書き保護
                self.graph.config_load(self)
                self.graph.commandword = protected_values
            case "ranking":
                protected_values = self.ranking.commandword  # 上書き保護
                self.ranking.config_load(self)
                self.ranking.commandword = protected_values
            case "report":
                protected_values = self.report.commandword  # 上書き保護
                self.report.config_load(self)
                self.report.commandword = protected_values
            case _:
                return
