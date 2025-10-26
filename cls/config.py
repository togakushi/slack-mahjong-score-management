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
from types import NoneType, UnionType
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeAlias, Union

from libs.types import GradeTableDict

if TYPE_CHECKING:
    from configparser import SectionProxy

SubClassType: TypeAlias = Union[
    "MahjongSection",
    "SettingSection",
    "MemberSection",
    "TeamSection",
    "AliasSection",
    "CommentSection",
    "DropItems",
    "BadgeDisplay",
    "SubCommand",
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
            if k in self.__dict__:
                match type(self.__dict__.get(k)):
                    case v_type if v_type is str:
                        setattr(self, k, self._section.get(k, fallback=self.get(k)))
                    case v_type if v_type is int:
                        setattr(self, k, self._section.getint(k, fallback=self.get(k)))
                    case v_type if v_type is float:
                        setattr(self, k, self._section.getfloat(k, fallback=self.get(k)))
                    case v_type if v_type is bool:
                        setattr(self, k, self._section.getboolean(k, fallback=self.get(k)))
                    case v_type if v_type is list:
                        v_list = [x.strip() for x in self._section.get(k, fallback=self.get(k)).split(",")]
                        current_list = getattr(self, k)
                        if isinstance(current_list, list) and current_list:  # 設定済みリストは追加
                            current_list.extend(v_list)
                        else:
                            setattr(self, k, v_list)
                    case v_type if v_type is UnionType:  # 文字列 or None
                        if set(v_type.__args__) == {str, type(None)}:
                            setattr(self, k, self._section.get(k, fallback=self.get(k)))
                    case v_type if v_type is PosixPath:
                        setattr(self, k, Path(self._section.get(k, fallback=self.get(k))))
                    case v_type if v_type is NoneType:
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
    """mahjongセクション初期値"""

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
    - True: なし
    - False: あり
    """
    draw_split: bool
    """同点時の順位点
    - True: 山分けにする
    - False: 席順で決める
    """
    regulations_type2: list
    """メモで役満として扱う単語リスト(カンマ区切り)"""

    def __init__(self, outer: "AppConfig", section_name):
        self._parser = outer._parser

        # 初期値セット
        self.rule_version = ""
        self.origin_point = 250
        self.return_point = 300
        self.rank_point = []
        self.ignore_flying = False
        self.draw_split = False
        self.regulations_type2 = []

        # 設定値取り込み
        super().__init__(self, section_name)

        # 順位点更新
        if not self.rank_point:
            self.rank_point = [30, 10, -10, -30]

        self.rank_point = list(map(int, self.rank_point))  # 数値化


class SettingSection(BaseSection):
    """settingセクション初期値"""

    help: str
    """ヘルプ表示キーワード"""

    keyword: str
    """成績記録キーワード"""
    remarks_word: str
    """メモ記録用キーワード"""

    time_adjust: int
    """日付変更後、集計範囲に含める追加時間"""
    guest_mark: str
    """ゲスト無効時に未登録メンバーに付与する印"""

    database_file: Union[Path, str]
    """成績管理データベースファイル名"""
    backup_dir: Optional[Path]
    """バックアップ先ディレクトリ"""

    font_file: Path
    """グラフ描写に使用するフォントファイル"""
    graph_style: str
    """グラフスタイル"""
    work_dir: Path
    """生成したファイルを保存するディレクトリ"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser

        # 初期値セット
        self.help = "麻雀成績ヘルプ"
        self.keyword = "終局"
        self.remarks_word = "麻雀成績メモ"
        self.time_adjust = 12
        self.guest_mark = "※"
        self.database_file = Path("mahjong.db")
        self.backup_dir = None
        self.font_file = Path("ipaexg.ttf")
        self.graph_style = "ggplot"
        self.work_dir = Path("work")

        # 設定値取り込み
        super().__init__(self, section_name)

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
        for chk_dir in (outer.config_dir, outer.script_dir):
            chk_file = chk_dir / str(self.database_file)
            if chk_file.exists():
                self.database_file = chk_file
                break

        if isinstance(self.backup_dir, PosixPath):
            try:
                self.backup_dir.mkdir(exist_ok=True)
            except FileExistsError as err:
                sys.exit(str(err))


class MemberSection(BaseSection):
    "memberセクション初期値"""

    registration_limit: int
    """登録メンバー上限数"""
    character_limit: int
    """名前に使用できる文字数"""
    alias_limit: int
    """別名登録上限数"""
    guest_name: str
    """未登録メンバー名称"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser

        # 初期値セット
        self.registration_limit = 255
        self.character_limit = 8
        self.alias_limit = 16
        self.guest_name = "ゲスト"

        # 設定値取り込み
        super().__init__(self, section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get("member", "commandword", fallback="メンバー一覧").split(",")]


class TeamSection(BaseSection):
    """teamセクション初期値"""

    registration_limit: int
    """登録チーム上限数"""
    character_limit: int
    """チーム名に使用できる文字数"""
    member_limit: int
    """チームに所属できるメンバー上限"""
    friendly_fire: bool
    """チームメイトが同卓しているゲームを集計対象に含めるか"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser

        # 初期値セット
        self.registration_limit = 255
        self.character_limit = 16
        self.member_limit = 16
        self.friendly_fire = True

        # 設定値取り込み
        super().__init__(self, section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get("team", "commandword", fallback="チーム一覧").split(",")]


class AliasSection(BaseSection):
    """aliasセクション初期値"""

    results: list
    graph: list
    ranking: list
    report: list
    download: list
    member: list
    add: list
    delete: list  # "del"はbuilt-inで使用
    team_create: list
    team_del: list
    team_add: list
    team_remove: list
    team_list: list
    team_clear: list

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser

        # 初期値セット
        self.results = ["成績"]
        self.graph = ["グラフ"]
        self.ranking = ["ランキング"]
        self.report = ["レポート"]
        self.download = ["ダウンロード"]
        self.member = ["userlist", "member_list"]
        self.add = []
        self.delete = ["del"]  # "del"はbuilt-inで使用
        self.team_create = []
        self.team_del = []
        self.team_add = []
        self.team_remove = []
        self.team_list = []
        self.team_clear = []

        # 設定値取り込み
        super().__init__(self, section_name)

        # デフォルト値として自身と同じ名前のコマンドを登録する #
        for k in self.to_dict():
            current_list = getattr(self, k)
            if isinstance(current_list, list):
                current_list.append(k)
        # delのエイリアス取り込み(設定ファイルに`delete`と書かれていない)
        list_data = [x.strip() for x in str(self._parser.get("alias", "del", fallback="")).split(",")]
        self.delete.extend(list_data)


class CommentSection(BaseSection):
    """commentセクション初期値"""

    group_length: int
    """コメント検索時の集約文字数(固定指定)"""
    search_word: str
    """コメント検索時の検索文字列(固定指定)"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser

        # 初期値セット
        self.group_length = 0
        self.search_word = ""

        # 設定値取り込み
        super().__init__(self, section_name)


class DropItems(BaseSection):
    """非表示項目リスト"""

    results: list
    ranking: list
    report: list

    def __init__(self, outer: "AppConfig"):
        self._parser = outer._parser

        # 初期値セット
        self.results = []
        self.ranking = []
        self.report = []

        # 設定値取り込み
        super().__init__(self, "")

        self.results = [x.strip() for x in self._parser.get("results", "dropitems", fallback="").split(",")]
        self.ranking = [x.strip() for x in self._parser.get("ranking", "dropitems", fallback="").split(",")]
        self.report = [x.strip() for x in self._parser.get("report", "dropitems", fallback="").split(",")]


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
    """サブコマンド共通クラス"""

    # 各種パラメータ
    section: str

    commandword: list
    """呼び出しキーワード"""

    aggregation_range: str
    """検索範囲未指定時に使用される範囲"""
    individual: bool
    """個人/チーム集計切替フラグ
    - True: 個人集計
    - False: チーム集計
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
    - True: 置き換える
    - False: 置き換えない
    """
    anonymous: bool
    """匿名化フラグ"""
    verbose: bool
    """詳細情報出力フラグ"""
    versus_matrix: bool
    """対戦マトリックス表示"""
    collection: str
    search_word: str
    group_length: int
    always_argument: list
    """オプションとして常に付与される文字列"""
    format: str
    filename: str
    interval: int

    def __init__(self, outer: "AppConfig", section_name: str, default: str):
        self._parser = outer._parser
        self.section = section_name

        # 初期値セット
        self.section = ""
        self.commandword = []
        self.aggregation_range: str = "当日"
        self.individual = True
        self.all_player = False
        self.daily = True
        self.fourfold = True
        self.game_results = False
        self.guest_skip = True
        self.guest_skip2 = True
        self.ranked = 3
        self.score_comparisons = False
        self.statistics = False
        self.stipulated = 0
        self.stipulated_rate = 0.05
        self.unregistered_replace = True
        self.anonymous = False
        self.verbose = False
        self.versus_matrix = False
        self.collection = ""
        self.search_word = ""
        self.group_length = 0
        self.always_argument = []
        self.format = ""
        self.filename = ""
        self.interval = 80

        # 設定値取り込み
        super().__init__(self, section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get(section_name, "commandword", fallback=default).split(",")]

    def stipulated_calculation(self, game_count: int) -> int:
        """規定打数をゲーム数から計算

        Args:
            game_count (int): 指定ゲーム数

        Returns:
            int: 規定ゲーム数
        """

        return int(ceil(game_count * self.stipulated_rate) + 1)


class AppConfig:
    """コンフィグ解析クラス"""

    def __init__(self, config_file: str):
        _config = Path(config_file)
        try:
            self._parser = ConfigParser()
            self._parser.read(_config, encoding="utf-8")
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
            "comment",
            "regulations",
        ]
        for x in option_sections:
            if x not in self._parser.sections():
                self._parser.add_section(x)

        # set base directory
        self.script_dir = Path(sys.argv[0]).absolute().parent
        """スクリプトが保存されているディレクトリパス"""
        self.config_dir = _config.absolute().parent
        """設定ファイルが保存されているディレクトリパス"""

        # 設定値取り込み
        self.setting = SettingSection(self, "setting")
        """settingセクション設定値"""
        self.mahjong = MahjongSection(self, "mahjong")
        """mahjongセクション設定値"""
        self.member = MemberSection(self, "member")
        """memberセクション設定値"""
        self.team = TeamSection(self, "team")
        """teamセクション設定値"""
        self.alias = AliasSection(self, "alias")
        """aliasセクション設定値"""
        self.comment = CommentSection(self, "comment")
        """commentセクション設定値"""
        self.dropitems = DropItems(self)  # 非表示項目
        """非表示項目"""
        self.badge = BadgeDisplay(self)  # バッジ表示
        """バッジ設定"""

        # サブコマンド
        self.results = SubCommand(self, "results", "麻雀成績")
        """resultsセクション設定値"""
        self.graph = SubCommand(self, "graph", "麻雀グラフ")
        """graphセクション設定値"""
        self.ranking = SubCommand(self, "ranking", "麻雀ランキング")
        """rankingセクション設定値"""
        self.report = SubCommand(self, "report", "麻雀成績レポート")
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

    def word_list(self) -> list:
        """設定されている値、キーワードをリスト化する

        Returns:
            list: リスト化されたキーワード
        """

        words: list = [
            [self.setting.keyword],
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

        words = list(set(chain.from_iterable(words)))  # 重複排除/平滑化
        words = [x for x in words if x != ""]  # 空文字削除

        return words
