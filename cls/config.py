"""
cls/config2.py
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
    def __init__(self):
        self._section = cast(SectionProxy, self._section)

    def get(self, key: str, fallback: Any = None) -> Any:
        return self._section.get(key, fallback)

    def getint(self, key: str, fallback: int = 0) -> int:
        return self._section.getint(key, fallback)

    def getfloat(self, key: str, fallback: float = 0.0) -> float:
        return self._section.getfloat(key, fallback)

    def getboolean(self, key: bool, fallback: bool = False) -> bool:
        return self._section.getboolean(key, fallback)

    def getlist(self, key: str) -> list:
        return [x.strip() for x in self._section.get(key, "").split(",")]

    def keys(self):
        return self._section.keys()

    def values(self):
        return self._section.values()

    def items(self):
        return self._section.items()

    def as_dict(self) -> dict[str, str]:
        return dict(self._section.items())


class BaseSection(CommonMethodMixin):
    """共通処理"""
    def __init__(self, outer, section_name: str):
        parser = cast(ConfigParser, outer._parser)
        if section_name not in parser:
            return
        self._section = parser[section_name]

        for k in self._section.keys():
            if k in self.__dict__:
                match type(self.__dict__.get(k)):
                    case v_type if v_type is type(str()):
                        setattr(self, k, self.get(k))
                    case v_type if v_type is type(int()):
                        setattr(self, k, self.getint(k))
                    case v_type if v_type is type(float()):
                        setattr(self, k, self.getfloat(k))
                    case v_type if v_type is type(bool()):
                        setattr(self, k, self.getboolean(k))
                    case v_type if v_type is type([]):
                        setattr(self, k, self.getlist(k))
                    case v_type if isinstance(v_type, UnionType):
                        if set(v_type.__args__) == {str, type(None)}:
                            setattr(self, k, self.get(k))
                    case _:
                        setattr(self, k, self.__dict__.get(k))

        logging.info("%s=%s", section_name, self.__dict__)

    def default_load(self) -> dict:
        """クラス変数からデフォルト値の取り込み"""
        return {k: v for k, v in self.__class__.__dict__.items() if not k.startswith("__") and not callable(v)}

    def to_dict(self) -> dict:
        """必要なパラメータを辞書型で返す

        Returns:
            dict: 返却値
        """

        ret_dict = self.__dict__
        for key in ["_parser", "_section", "always_argument"]:
            if key in ret_dict:
                ret_dict.pop(key)

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
    slash_command: str = "/mahjong"
    """スラッシュコマンド名"""
    thread_report: bool = True
    """スレッド内にある得点報告を扱う"""
    time_adjust: int = 12
    """日付変更後、集計範囲に含める追加時間"""
    guest_mark: str = "※"
    """ゲスト無効時に未登録メンバーに付与する印"""
    reaction_ok: str = "ok"
    """DBに取り込んだ時に付けるリアクション"""
    reaction_ng: str = "ng"
    """DBに取り込んだが正確な値ではない可能性があるときに付けるリアクション"""
    font_file: str = "ipaexg.ttf"
    """グラフ描写に使用するフォントファイル"""
    graph_style: str = "ggplot"
    """グラフスタイル"""
    work_dir: str = "work"
    """生成したファイルを保存するディレクトリ"""
    ignore_userid: list = []
    """投稿を無視するユーザのリスト(カンマ区切りで設定)"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
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

        logging.notice("font file: %s", self.font_file)


class SearchSection(BaseSection):
    """searchセクション初期値"""
    keyword: str = "終局"
    """成績記録キーワード"""
    channel: str | None = None
    """テータ突合時に成績記録ワードを検索するチャンネル名"""
    after: int = 7
    """データ突合時対象にする日数"""
    wait: int = 180
    """指定秒数以内にポストされているデータは突合対象から除外する"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)


class DatabaseSection(BaseSection):
    """databaseセクション初期値"""
    database_file: str = "mahjong.db"
    """成績管理データベースファイル名"""
    channel_limitations: list = []
    """SQLを実行できるチャンネルリスト"""
    backup_dir: str | None = None
    """バックアップ先ディレクトリ"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)

        self.database_file = os.path.realpath(os.path.join(outer.config_dir, self.database_file))
        if self.backup_dir:
            self.backup_dir = os.path.realpath(os.path.join(outer.script_dir, self.backup_dir))

        logging.notice("database: %s", self.database_file)  # type: ignore


class MemberSection(BaseSection):
    registration_limit: int = 255
    """登録メンバー上限数"""
    character_limit: int = 8
    """名前に使用できる文字数"""
    alias_limit: int = 16
    """別名登録上限数"""
    guest_name: str = "ゲスト"
    """未登録メンバー名称"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)


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

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)


class AliasSection(BaseSection):
    """aliasセクション初期値"""
    results: list = []
    graph: list = []
    ranking: list = []
    report: list = []
    check: list = []
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

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)

        # デフォルト値として自身と同じ名前のコマンドを登録する #
        parser = cast(ConfigParser, outer._parser)
        for k in self.to_dict().keys():
            cast(list, getattr(self, k)).append(k)
        self.delete.append("del")
        list_data = [x.strip() for x in str(parser.get("alias", "del", fallback="")).split(",")]
        self.delete.extend(list_data)


class CommentSection(BaseSection):
    """commentセクション初期値"""
    group_length: int = 0
    """コメント検索時の集約文字数(固定指定)"""
    search_word: str = ""
    """コメント検索時の検索文字列(固定指定)"""

    def __init__(self, outer, section_name):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, section_name)


class CommandWord(BaseSection):
    """チャンネル内呼び出しキーワード初期値"""
    help: str = "ヘルプ"
    results: str = "麻雀成績"
    graph: str = "麻雀グラフ"
    ranking: str = "麻雀ランキング"
    report: str = "麻雀成績レポート"
    member: str = "メンバー一覧"
    team: str = "チーム一覧"
    remarks_word: str = "麻雀成績メモ"
    check: str = "麻雀成績チェック"

    def __init__(self, outer):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, "")

        self.help = self._parser.get("help", "commandword", fallback=CommandWord.help)
        self.results = self._parser.get("results", "commandword", fallback=CommandWord.results)
        self.graph = self._parser.get("graph", "commandword", fallback=CommandWord.graph)
        self.ranking = self._parser.get("ranking", "commandword", fallback=CommandWord.ranking)
        self.report = self._parser.get("report", "commandword", fallback=CommandWord.report)
        self.member = self._parser.get("member", "commandword", fallback=CommandWord.member)
        self.team = self._parser.get("team", "commandword", fallback=CommandWord.team)
        self.remarks_word = self._parser.get("setting", "remarks_word", fallback=CommandWord.remarks_word)
        self.check = self._parser.get("database", "commandword", fallback=CommandWord.check)


class DropItems(BaseSection):
    """非表示項目リスト"""
    results: list = []
    ranking: list = []
    report: list = []

    def __init__(self, outer):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, "")

        self.results = [x.strip() for x in self._parser.get("results", "dropitems", fallback="").split(",")]
        self.ranking = [x.strip() for x in self._parser.get("ranking", "dropitems", fallback="").split(",")]
        self.report = [x.strip() for x in self._parser.get("report", "dropitems", fallback="").split(",")]


class BadgeDisplay(BaseSection):
    """バッジ表示"""
    @dataclass
    class BadgeGradeSpec:
        """段位"""
        display: bool = field(default=False)
        table_name: str = field(default=str())
        table: GradeTableDict = field(default_factory=lambda: cast(GradeTableDict, dict))

    degree: bool = False
    status: bool = False
    grade: BadgeGradeSpec = BadgeGradeSpec

    def __init__(self, outer):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        super().__init__(self, "")

        self.degree = self._parser.getboolean("degree", "display", fallback=False)
        self.status = self._parser.getboolean("status", "display", fallback=False)
        self.grade.display = self._parser.getboolean("grade", "display", fallback=False)
        self.grade.table_name = self._parser.get("grade", "table_name", fallback="")


class SubCommand(BaseSection):
    """サブコマンド共通クラス"""
    section: str | None = None
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
    """オプションとして常に付与される文字列(カンマ区切り)"""
    format: str = ""
    filename: str = ""
    interval: int = 80

    def __init__(self, outer, section_name: str):
        self._parser = cast(ConfigParser, outer._parser)
        self.__dict__.update(super().default_load())
        self.section = section_name
        super().__init__(self, section_name)

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
            logging.notice("configfile: %s", path)  # type: ignore
        except Exception as e:
            raise RuntimeError(e) from e

        # 必須セクションチェック
        for x in ("mahjong", "setting"):
            if x not in self._parser.sections():
                logging.critical("Required section not found. (%s)", x)
                sys.exit(255)

        # オプションセクションチェック
        for x in ("results", "graph", "ranking", "report", "member", "alias", "team", "database", "comment", "regulations", "help"):
            if x not in self._parser.sections():
                self._parser.add_section(x)

        # set base directory
        self.script_dir = os.path.realpath(str(Path(__file__).resolve().parents[1]))
        self.config_dir = os.path.dirname(os.path.realpath(str(path)))
        logging.info("script_dir=%s, config_dir=%s", self.script_dir, self.config_dir)

        # 設定値取り込み
        self.mahjong = MahjongSection(self, "mahjong")
        self.setting = SettingSection(self, "setting")
        self.search = SearchSection(self, "search")
        self.db = DatabaseSection(self, "database")
        self.member = MemberSection(self, "member")
        self.team = TeamSection(self, "team")
        self.alias = AliasSection(self, "alias")
        self.comment = CommentSection(self, "comment")
        self.cw = CommandWord(self)  # チャンネル内呼び出しキーワード
        self.dropitems = DropItems(self)  # 非表示項目
        self.badge = BadgeDisplay(self)  # バッジ表示

        # サブコマンドデフォルト
        self.results = SubCommand(self, "results")
        self.graph = SubCommand(self, "graph")
        self.ranking = SubCommand(self, "ranking")
        self.report = SubCommand(self, "report")

        # 共通設定値
        self.undefined_word: int = 0
        self.aggregate_unit: str = ""

    def word_list(self) -> list:
        """設定されている値、キーワードをリスト化する

        Returns:
            list: リスト化されたキーワード
        """

        words: list = []

        words.append([self.setting.slash_command])
        words.append([self.search.keyword])

        for x in self.cw.to_dict().values():
            words.append([x])

        for k, v in self.alias.to_dict().items():
            if isinstance(v, list):
                words.append([k])
                words.append(v)

        words = list(set(chain.from_iterable(words)))
        words = ["del" if x == "delete" else x for x in words]
        words = [x for x in words if x != ""]

        return words
