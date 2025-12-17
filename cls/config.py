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

    from libs.types import TeamDataDict

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
                    case v_type if v_type is Optional[str]:  # 文字列 or None(未定義)
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
    """mahjongセクション"""

    def __init__(self):
        self.rule_version: str = ""
        """ルール判別識別子"""
        self.origin_point: int = 250
        """配給原点"""
        self.return_point: int = 300
        """返し点"""
        self.rank_point: list = []
        """順位点"""
        self.ignore_flying: bool = False
        """トビカウント
        - *True*: なし
        - *False*: あり
        """
        self.draw_split: bool = False
        """同点時の順位点
        - *True*: 山分けにする
        - *False*: 席順で決める
        """
        self.separate: bool = False
        """スコア入力元識別子別集計フラグ
        - *True*: 識別子別に集計
        - *False*: すべて集計
        """
        self.regulations_type2: list = []
        """メモで役満として扱う単語リスト(カンマ区切り)"""

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "mahjong"
        self._parser = outer._parser
        self.__init__()
        super().__init__(self, _section_name)

        # 順位点更新
        if not self.rank_point:
            self.rank_point = [30, 10, -10, -30]
        self.rank_point = list(map(int, self.rank_point[:4]))  # 数値化

        logging.debug("%s: %s", _section_name, self)


class SettingSection(BaseSection):
    """settingセクション"""

    def __init__(self):
        self.help: str = "麻雀成績ヘルプ"
        """ヘルプ表示キーワード"""
        self.keyword: str = "終局"
        """成績記録キーワード(プライマリ)"""
        self.remarks_word: str = "麻雀成績メモ"
        """メモ記録用キーワード"""
        self.time_adjust: int = 12
        """日付変更後、集計範囲に含める追加時間"""
        self.search_word: str = ""
        """コメント固定(検索時の検索文字列)"""
        self.group_length: int = 0
        """コメント固定(検索時の集約文字数)"""
        self.guest_mark: str = "※"
        """ゲスト無効時に未登録メンバーに付与する印"""
        self.database_file: Union[Path, str] = Path("mahjong.db")
        """成績管理データベースファイル名"""
        self.backup_dir: Optional[Path] = None
        """バックアップ先ディレクトリ"""
        self.font_file: Path = Path("ipaexg.ttf")
        """グラフ描写に使用するフォントファイル"""
        self.graph_style: str = "ggplot"
        """グラフスタイル"""
        self.work_dir: Path = Path("work")

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "setting"
        self._parser = outer._parser
        self.__init__()
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

        logging.debug("%s: %s", _section_name, self)


class MemberSection(BaseSection):
    """memberセクション"""

    def __init__(self):
        self.list: dict[str, str] = {}
        """メンバーリスト"""
        self.registration_limit: int = 255
        """登録メンバー上限数"""
        self.character_limit: int = 8
        """名前に使用できる文字数"""
        self.alias_limit: int = 16
        """別名登録上限数"""
        self.guest_name: str = "ゲスト"
        """未登録メンバー名称"""

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "member"
        self._parser = outer._parser
        self.__init__()
        super().__init__(self, _section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get(_section_name, "commandword", fallback="メンバー一覧").split(",")]

        logging.debug("%s: %s", _section_name, self)


class TeamSection(BaseSection):
    """teamセクション"""

    def __init__(self):
        self.list: list["TeamDataDict"] = []
        """チームリスト"""
        self.registration_limit: int = 255
        """登録チーム上限数"""
        self.character_limit: int = 16
        """チーム名に使用できる文字数"""
        self.member_limit: int = 16
        """チームに所属できるメンバー上限"""
        self.friendly_fire: bool = True
        """チームメイトが同卓しているゲームを集計対象に含めるか"""

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "team"
        self._parser = outer._parser
        self.__init__()
        super().__init__(self, _section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get(_section_name, "commandword", fallback="チーム一覧").split(",")]

        logging.debug("%s: %s", _section_name, self)


class AliasSection(BaseSection):
    """aliasセクション初期値"""

    def __init__(self):
        self.results: list = ["成績"]
        self.graph: list = ["グラフ"]
        self.ranking: list = ["ランキング"]
        self.report: list = ["レポート"]
        self.download: list = ["ダウンロード"]
        self.member: list = ["userlist", "member_list"]
        self.add: list = []
        self.delete: list = ["del"]  # "del"はbuilt-inで使用
        self.team_create: list = []
        self.team_del: list = []
        self.team_add: list = []
        self.team_remove: list = []
        self.team_list: list = []
        self.team_clear: list = []

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        _section_name: str = "alias"
        self._parser = outer._parser
        self.__init__()
        super().__init__(self, _section_name)

        # デフォルト値として自身と同じ名前のコマンドを登録する #
        for k in self.to_dict():
            current_list = getattr(self, k)
            if isinstance(current_list, list):
                current_list.append(k)
        # delのエイリアス取り込み(設定ファイルに`delete`と書かれていない)
        list_data = [x.strip() for x in str(self._parser.get("alias", "del", fallback="")).split(",")]
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
    """サブコマンドセクション"""

    def __init__(self, section_name: str):
        self.section = section_name
        """サブコマンドセクション名"""

        self.commandword: list = []
        """呼び出しキーワード"""
        self.aggregation_range: str = "当日"
        """検索範囲未指定時に使用される範囲"""
        self.individual: bool = True
        """個人/チーム集計切替フラグ
        - *True*: 個人集計
        - *False*: チーム集計
        """
        self.all_player: bool = False
        self.daily: bool = True
        self.fourfold: bool = True
        self.game_results: bool = False
        self.guest_skip: bool = True
        self.guest_skip2: bool = True
        self.ranked: int = 3
        self.score_comparisons: bool = False
        """スコア比較"""
        self.statistics: bool = False
        """統計情報表示"""
        self.stipulated: int = 0
        """規定打数指定"""
        self.stipulated_rate: float = 0.05
        """規定打数計算レート"""
        self.unregistered_replace: bool = True
        """メンバー未登録プレイヤー名をゲストに置き換えるかフラグ
        - *True*: 置き換える
        - *False*: 置き換えない
        """
        self.anonymous: bool = False
        """匿名化フラグ"""
        self.verbose: bool = False
        """詳細情報出力フラグ"""
        self.versus_matrix: bool = False
        """対戦マトリックス表示"""
        self.collection: str = ""
        self.always_argument: list = []
        """オプションとして常に付与される文字列"""
        self.format: str = ""
        self.filename: str = ""
        self.interval: int = 80

    def config_load(self, outer: "AppConfig"):
        """設定値取り込み

        Args:
            outer (AppConfig): 設定クラスオブジェクト
        """

        self._parser = outer._parser
        self.__init__(self.section)
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
    """secondary_keywordセクション初期値"""

    def __init__(self, outer: "AppConfig", section_name: str):
        self._parser = outer._parser
        self.rule: dict[str, Union[Path, str]] = {}

        # 設定値取り込み
        for k, v in self._parser.items(section_name):
            if (overwrite := Path(v)).exists():
                self.rule.update({f"{k}": overwrite})
            if v == "":
                self.rule.update({f"{k}": outer.config_file})


class AppConfig:
    """コンフィグ解析クラス"""

    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        try:
            self._parser = ConfigParser()
            self._parser.read(self.config_file, encoding="utf-8")
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

        # 成績記録キーワード
        self.keyword = KeywordMapping(self, "secondary_keyword")
        if not self.keyword.rule:
            self.keyword.rule = {self.setting.keyword: self.config_file}
        if self.setting.keyword not in self.keyword.rule:
            self.keyword.rule.update({self.setting.keyword: self.config_file})

        self.initialization()

    def initialization(self):
        """設定ファイル読み込み"""

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

    def overwrite(self, config_file: PosixPath, section_name: str):
        """指定セクションを上書き

        Args:
            config_file (PosixPath): 設定ファイルパス
            section_name (str): セクション名
        """

        if not config_file.exists:
            return

        try:
            self._parser = ConfigParser()
            self._parser.read(config_file, encoding="utf-8")
        except Exception as err:
            logging.error(err)
            return

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

        logging.debug("%s: %s", section_name, config_file)
