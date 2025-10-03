"""
cls/config.py
"""

import logging
import os
import sys
from configparser import ConfigParser, SectionProxy
from dataclasses import dataclass, field
from itertools import chain
from math import ceil
from pathlib import Path
from types import UnionType
from typing import Any, cast

from cls.types import GradeTableDict


class CommonMethodMixin:
    """共通メソッド"""

    _section: SectionProxy

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
        return cast(bool, self._section.getboolean(key, fallback))

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

    def __init__(self, outer, section_name: str):
        parser = cast(ConfigParser, outer._parser)
        if section_name not in parser:
            return
        self._section = parser[section_name]

        self.initialization()
        self.section = section_name  # セクション名保持
        logging.info("%s=%s", section_name, self)

    def __repr__(self) -> str:
        return str({k: v for k, v in vars(self).items() if not str(k).startswith("_")})

    def initialization(self):
        """設定ファイルから値の取り込み"""
        self.__dict__.update(self.default_load())
        for k in self._section.keys():
            if k in self.__dict__:
                match type(self.__dict__.get(k)):
                    case v_type if v_type is type(str()):
                        setattr(self, k, self._section.get(k, fallback=self.get(k)))
                    case v_type if v_type is type(int()):
                        setattr(self, k, self._section.getint(k, fallback=self.get(k)))
                    case v_type if v_type is type(float()):
                        setattr(self, k, self._section.getfloat(k, fallback=self.get(k)))
                    case v_type if v_type is type(bool()):
                        setattr(self, k, self._section.getboolean(k, fallback=self.get(k)))
                    case v_type if v_type is type([]):
                        v_list = [x.strip() for x in self._section.get(k, fallback=self.get(k)).split(",")]
                        setattr(self, k, v_list)
                    case v_type if isinstance(v_type, UnionType):
                        if set(v_type.__args__) == {str, type(None)}:
                            setattr(self, k, self._section.get(k, fallback=self.get(k)))
                    case v_type if v_type is type(None):
                        setattr(self, k, self._section.get(k, fallback=self.get(k)))
                    case _:
                        setattr(self, k, self.__dict__.get(k))

    def default_load(self) -> dict:
        """クラス変数からデフォルト値の取り込み"""
        return {k: v for k, v in self.__class__.__dict__.items() if not k.startswith("__") and not callable(v)}

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

    rule_version: str = str()
    """ルール判別識別子"""
    origin_point: int = 250
    """配給原点"""
    return_point: int = 300
    """返し点"""
    rank_point: list = [30, 10, -10, -30]
    """順位点"""
    ignore_flying: bool = False
    """トビカウント
    - True: なし
    - False: あり
    """
    draw_split: bool = False
    """同点時の順位点
    - True: 山分けにする
    - False: 席順で決める
    """
    regulations_type2: list = []
    """メモで役満として扱う単語リスト(カンマ区切り)"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)

        self.rank_point = list(map(int, self.rank_point))  # 数値化


class SettingSection(BaseSection):
    """settingセクション初期値"""

    help: str = "麻雀成績ヘルプ"
    """ヘルプ表示キーワード"""

    keyword: str = "終局"
    """成績記録キーワード"""
    remarks_word: str = "麻雀成績メモ"
    """メモ記録用キーワード"""

    time_adjust: int = 12
    """日付変更後、集計範囲に含める追加時間"""
    guest_mark: str = "※"
    """ゲスト無効時に未登録メンバーに付与する印"""

    database_file: str = "mahjong.db"
    """成績管理データベースファイル名"""
    backup_dir: str | None = None
    """バックアップ先ディレクトリ"""

    font_file: str = "ipaexg.ttf"
    """グラフ描写に使用するフォントファイル"""
    graph_style: str = "ggplot"
    """グラフスタイル"""
    work_dir: str = "work"
    """生成したファイルを保存するディレクトリ"""

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, section_name)

        self.work_dir = os.path.realpath(os.path.join(outer.script_dir, self.work_dir))

        # フォントファイルチェック
        for chk_dir in (outer.config_dir, outer.script_dir):
            chk_path = str(os.path.realpath(os.path.join(chk_dir, self.font_file)))
            if os.path.exists(chk_path):
                self.font_file = chk_path
                break

        if chk_path != self.font_file:
            logging.critical("The specified font file cannot be found.")
            sys.exit(255)

        # データベース関連
        self.database_file = os.path.realpath(os.path.join(outer.config_dir, self.database_file))
        if self.backup_dir:
            self.backup_dir = os.path.realpath(os.path.join(outer.script_dir, self.backup_dir))


class MemberSection(BaseSection):
    "memberセクション初期値"""

    registration_limit: int = 255
    """登録メンバー上限数"""
    character_limit: int = 8
    """名前に使用できる文字数"""
    alias_limit: int = 16
    """別名登録上限数"""
    guest_name: str = "ゲスト"
    """未登録メンバー名称"""

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get("member", "commandword", fallback="メンバー一覧").split(",")]


class TeamSection(BaseSection):
    """teamセクション初期値"""

    registration_limit: int = 255
    """登録チーム上限数"""
    character_limit: int = 16
    """チーム名に使用できる文字数"""
    member_limit: int = 16
    """チームに所属できるメンバー上限"""
    friendly_fire: bool = True
    """チームメイトが同卓しているゲームを集計対象に含めるか"""

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, section_name)

        # 呼び出しキーワード取り込み
        self.commandword = [x.strip() for x in self._parser.get("team", "commandword", fallback="チーム一覧").split(",")]


class AliasSection(BaseSection):
    """aliasセクション初期値"""

    results: list = []
    graph: list = []
    ranking: list = []
    report: list = []
    download: list = []
    member: list = []
    add: list = []
    delete: list = []  # "del"はbuilt-inで使用
    team_create: list = []
    team_del: list = []
    team_add: list = []
    team_remove: list = []
    team_list: list = []
    team_clear: list = []

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, section_name)

        # デフォルト値として自身と同じ名前のコマンドを登録する #
        parser = cast(ConfigParser, outer._parser)
        for k in self.to_dict():
            x = getattr(self, k)
            if isinstance(x, list):
                x.append(k)
        list_data = [x.strip() for x in str(parser.get("alias", "del", fallback="")).split(",")] + ["del"]
        self.delete.extend(list_data)


class CommentSection(BaseSection):
    """commentセクション初期値"""

    group_length: int = 0
    """コメント検索時の集約文字数(固定指定)"""
    search_word: str = ""
    """コメント検索時の検索文字列(固定指定)"""

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, section_name)


class DropItems(BaseSection):
    """非表示項目リスト"""

    results: list = []
    ranking: list = []
    report: list = []

    def __init__(self, outer):
        self._parser = cast(ConfigParser, outer._parser)
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
        table: GradeTableDict = field(default_factory=lambda: cast(GradeTableDict, dict))

    grade: "BadgeGradeSpec" = BadgeGradeSpec()

    def __init__(self, outer):
        self._parser = cast(ConfigParser, outer._parser)
        super().__init__(self, "")

        self.grade.table_name = self._parser.get("grade", "table_name", fallback="")


class SubCommand(BaseSection):
    """サブコマンド共通クラス"""

    # 各種パラメータ
    section: str = ""

    commandword: list = []
    """呼び出しキーワード"""

    aggregation_range: str = "当日"
    """検索範囲未指定時に使用される範囲"""
    individual: bool = True
    """個人/チーム集計切替フラグ
    - True: 個人集計
    - False: チーム集計
    """
    all_player: bool = False
    daily: bool = True
    fourfold: bool = True
    game_results: bool = False
    guest_skip: bool = True
    guest_skip2: bool = True
    ranked: int = 3
    score_comparisons: bool = False
    """スコア比較"""
    statistics: bool = False
    """統計情報表示"""
    stipulated: int = 1
    """規定打数指定"""
    stipulated_rate: float = 0.05
    """規定打数計算レート"""
    unregistered_replace: bool = True
    """メンバー未登録プレイヤー名をゲストに置き換えるかフラグ
    - True: 置き換える
    - False: 置き換えない
    """
    anonymous: bool = False
    """匿名化フラグ"""
    verbose: bool = False
    """詳細情報出力フラグ"""
    versus_matrix: bool = False
    """対戦マトリックス表示"""
    collection: str = ""
    search_word: str = ""
    group_length: int = 0
    always_argument: list = []
    """オプションとして常に付与される文字列"""
    format: str = ""
    filename: str = ""
    interval: int = 80

    def __init__(self, outer, section_name: str, default: str):
        self._parser = cast(ConfigParser, outer._parser)
        self.section = section_name
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

    def __init__(self, path: str):
        path = os.path.realpath(path)
        try:
            self._parser = ConfigParser()
            self._parser.read(path, encoding="utf-8")
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
        self.script_dir = os.path.realpath(str(Path(__file__).resolve().parents[1]))
        self.config_dir = os.path.dirname(os.path.realpath(str(path)))

        # 設定値取り込み
        self.mahjong = MahjongSection(self, "mahjong")
        self.setting = SettingSection(self, "setting")
        self.member = MemberSection(self, "member")
        self.team = TeamSection(self, "team")
        self.alias = AliasSection(self, "alias")
        self.comment = CommentSection(self, "comment")
        self.dropitems = DropItems(self)  # 非表示項目
        self.badge = BadgeDisplay(self)  # バッジ表示

        # サブコマンド
        self.results = SubCommand(self, "results", "麻雀成績")
        self.graph = SubCommand(self, "graph", "麻雀グラフ")
        self.ranking = SubCommand(self, "ranking", "麻雀ランキング")
        self.report = SubCommand(self, "report", "麻雀成績レポート")

        # 共通設定値
        self.undefined_word: int = 0
        self.aggregate_unit: str = ""

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
