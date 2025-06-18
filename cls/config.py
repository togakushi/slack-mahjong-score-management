"""
cls/config.py
"""

import configparser
import logging
import os
import sys
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import cast

from cls.mixin import CommonMethodMixin
from cls.subcom import SubCommand
from cls.types import GradeTableDict


@dataclass
class MahjongSection(CommonMethodMixin):
    """mahjongセクション初期値"""
    _config: configparser.ConfigParser | None = None
    rule_version: str = field(default=str())
    """ルール判別識別子"""
    origin_point: int = field(default=250)
    """配給原点"""
    return_point: int = field(default=300)
    """返し点"""
    rank_point: list = field(default_factory=list)
    """順位点"""
    ignore_flying: bool = field(default=False)
    """トビカウント
    - True: なし
    - False: あり
    """
    draw_split: bool = field(default=False)
    """同点時の順位点
    - True: 山分けにする
    - False: 席順で決める
    """
    regulations_type2: list = field(default_factory=list)
    """メモで役満として扱う単語リスト(カンマ区切り)"""

    def __post_init__(self):
        self.initialization("mahjong")
        self.rank_point = list(map(int, self.rank_point))  # 数値化
        if not self.rank_point:
            self.rank_point = [30, 10, -10, -30]


@dataclass
class SettingSection(CommonMethodMixin):
    """settingセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    slash_command: str = field(default="/mahjong")
    """スラッシュコマンド名"""
    thread_report: bool = field(default=True)
    """スレッド内にある得点報告を扱う"""
    time_adjust: int = field(default=12)
    """日付変更後、集計範囲に含める追加時間"""
    guest_mark: str = field(default="※")
    """ゲスト無効時に未登録メンバーに付与する印"""
    reaction_ok: str = field(default="ok")
    """DBに取り込んだ時に付けるリアクション"""
    reaction_ng: str = field(default="ng")
    """DBに取り込んだが正確な値ではない可能性があるときに付けるリアクション"""
    font_file: str = field(default="ipaexg.ttf")
    """グラフ描写に使用するフォントファイル"""
    graph_style: str = field(default="ggplot")
    """グラフスタイル"""
    work_dir: str = field(default="work")
    """生成したファイルを保存するディレクトリ"""
    ignore_userid: list = field(default_factory=list)
    """投稿を無視するユーザのリスト(カンマ区切りで設定)"""

    def __post_init__(self):
        self.initialization("setting")


@dataclass
class SearchSection(CommonMethodMixin):
    """searchセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    keyword: str = field(default="終局")
    """成績記録キーワード"""
    channel: str | None = field(default=None)
    """テータ突合時に成績記録ワードを検索するチャンネル名"""
    after: int = field(default=7)
    """データ突合時対象にする日数"""
    wait: int = field(default=180)
    """指定秒数以内にポストされているデータは突合対象から除外する"""

    def __post_init__(self):
        self.initialization("search")


@dataclass
class DatabaseSection(CommonMethodMixin):
    """databaseセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    database_file: str = field(default="mahjong.db")
    """成績管理データベースファイル名"""
    channel_limitations: list = field(default_factory=list)
    """SQLを実行できるチャンネルリスト"""
    backup_dir: str | None = field(default=None)
    """バックアップ先ディレクトリ"""

    def __post_init__(self):
        self.initialization("database")


@dataclass
class MemberSection(CommonMethodMixin):
    """memberセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    registration_limit: int = field(default=255)
    """登録メンバー上限数"""
    character_limit: int = field(default=8)
    """名前に使用できる文字数"""
    alias_limit: int = field(default=16)
    """別名登録上限数"""
    guest_name: str = field(default="ゲスト")
    """未登録メンバー名称"""

    def __post_init__(self):
        self.initialization("member")


@dataclass
class TeamSection(CommonMethodMixin):
    """teamセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    registration_limit: int = field(default=255)
    """登録チーム上限数"""
    character_limit: int = field(default=16)
    """チーム名に使用できる文字数"""
    member_limit: int = field(default=16)
    """チームに所属できるメンバー上限"""
    friendly_fire: bool = field(default=True)
    """チームメイトが同卓しているゲームを集計対象に含めるか"""

    def __post_init__(self):
        self.initialization("team")


@dataclass
class AliasSection(CommonMethodMixin):
    """aliasセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    results: list = field(default_factory=list)
    graph: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)
    check: list = field(default_factory=list)
    download: list = field(default_factory=list)
    member: list = field(default_factory=list)
    add: list = field(default_factory=list)
    delete: list = field(default_factory=list)  # delはbuilt-inで使用
    team_create: list = field(default_factory=list)
    team_del: list = field(default_factory=list)
    team_add: list = field(default_factory=list)
    team_remove: list = field(default_factory=list)
    team_list: list = field(default_factory=list)
    team_clear: list = field(default_factory=list)

    def __post_init__(self):
        self.initialization("alias")

        # デフォルト値として自身と同じ名前のコマンドを登録する #
        getattr(self, "delete").append("del")
        for name, typ in self.__class__.__annotations__.items():
            if typ == list:
                getattr(self, name).append(name)


@dataclass
class CommentSection(CommonMethodMixin):
    """commentセクション初期値"""
    _config: configparser.ConfigParser | None = field(default=None)
    group_length: int = field(default=0)
    """コメント検索時の集約文字数(固定指定)"""
    search_word: str = field(default=str())
    """コメント検索時の検索文字列(固定指定)"""

    def __post_init__(self):
        self.initialization("comment")


@dataclass
class CommandWord:
    """チャンネル内呼び出しキーワード初期値"""
    help: str = field(default="ヘルプ")
    results: str = field(default="麻雀成績")
    graph: str = field(default="麻雀グラフ")
    ranking: str = field(default="麻雀ランキング")
    report: str = field(default="麻雀成績レポート")
    member: str = field(default="メンバー一覧")
    team: str = field(default="チーム一覧")
    remarks_word: str = field(default="麻雀成績メモ")
    check: str = field(default="麻雀成績チェック")


@dataclass
class DropItems:
    """非表示項目リスト"""
    results: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)


@dataclass
class BadgeGradeSpec:
    """段位"""
    display: bool = field(default=False)
    table_name: str = field(default=str())
    table: GradeTableDict = field(default_factory=lambda: cast(GradeTableDict, dict))


@dataclass
class BadgeDisplay:
    """バッジ表示"""
    degree: bool = field(default=False)
    status: bool = field(default=False)
    grade: BadgeGradeSpec = field(default_factory=BadgeGradeSpec)


class Config:
    """コンフィグ解析クラス"""
    # コンフィグセクション
    mahjong: MahjongSection
    setting: SettingSection
    search: SearchSection
    db: DatabaseSection
    member: MemberSection
    team: TeamSection
    alias: AliasSection
    comment: CommentSection
    dropitems: DropItems
    badge: BadgeDisplay
    cw: CommandWord
    # サブコマンド
    results: SubCommand
    graph: SubCommand
    ranking: SubCommand
    report: SubCommand

    def __init__(self, filename: str) -> None:
        """サブクラスのセットアップ、設定ファイルの読み込み

        Args:
            filename (str): 設定ファイル
        """

        # 共通パラメータ
        self._config: configparser.ConfigParser
        self.script_dir: str
        """メインスクリプト格納ディレクトリ"""
        self.config_dir: str
        """設定ファイル格納ディレクトリ"""
        self.format: str
        self.filename: str
        self.interval: int
        self.aggregate_unit: str
        self.undefined_word: int

        self.read_file(filename)

    def read_file(self, filename: str) -> None:
        """設定ファイル読み込み

        Args:
            str: 設定ファイル
        Raises:
            RuntimeError: 設定ファイル読み込み失敗
            """

        # set base directory
        self.script_dir = os.path.realpath(str(Path(__file__).resolve().parents[1]))
        self.config_dir = os.path.dirname(os.path.realpath(str(filename)))
        logging.info("script_dir=%s, config_dir=%s", self.script_dir, self.config_dir)

        try:
            self._config = configparser.ConfigParser()
            self._config.read(os.path.realpath(filename), encoding="utf-8")
            logging.notice("configfile: %s", os.path.realpath(filename))  # type: ignore
            logging.info("read sections: %s", self._config.sections())
        except Exception as e:
            raise RuntimeError(e) from e

        # 必須セクションチェック
        for x in ("mahjong", "setting"):
            if x not in self._config.sections():
                logging.critical("Required section not found. (%s)", x)
                sys.exit(255)

        # オプションセクションチェック
        for x in ("results", "graph", "ranking", "report", "member", "alias", "team", "database", "comment", "regulations", "help"):
            if x not in self._config.sections():
                self._config.add_section(x)

        # セクション読み込み
        Config.mahjong = MahjongSection(self._config)
        Config.setting = SettingSection(self._config)
        Config.search = SearchSection(self._config)
        Config.db = DatabaseSection(self._config)
        Config.member = MemberSection(self._config)
        Config.team = TeamSection(self._config)
        Config.alias = AliasSection(self._config)
        Config.comment = CommentSection(self._config)
        Config.cw = CommandWord(  # チャンネル内呼び出しキーワード
            help=self._config["help"].get("commandword", CommandWord.help),
            results=self._config["results"].get("commandword", CommandWord.results),
            graph=self._config["graph"].get("commandword", CommandWord.graph),
            ranking=self._config["ranking"].get("commandword", CommandWord.ranking),
            report=self._config["report"].get("commandword", CommandWord.report),
            member=self._config["member"].get("commandword", CommandWord.member),
            team=self._config["team"].get("commandword", CommandWord.team),
            remarks_word=self._config["setting"].get("remarks_word", CommandWord.remarks_word),
            check=self._config["database"].get("commandword", CommandWord.check),
        )
        Config.dropitems = DropItems(  # 非表示項目リスト
            results=[x.strip() for x in self._config["results"].get("dropitems", "").split(",")],
            ranking=[x.strip() for x in self._config["ranking"].get("dropitems", "").split(",")],
            report=[x.strip() for x in self._config["report"].get("dropitems", "").split(",")],
        )

        # バッジ表示
        Config.badge = BadgeDisplay()
        if "degree" in self._config.sections():
            Config.badge.degree = self._config.getboolean("degree", "display", fallback=False)
        if "status" in self._config.sections():
            Config.badge.status = self._config.getboolean("status", "display", fallback=False)
        if "grade" in self._config.sections():
            Config.badge.grade.display = self._config.getboolean("grade", "display", fallback=False)
            Config.badge.grade.table_name = self._config.get("grade", "table_name", fallback="")

        # サブコマンドデフォルト
        Config.results = SubCommand(self._config, "results")
        Config.graph = SubCommand(self._config, "graph")
        Config.ranking = SubCommand(self._config, "ranking")
        Config.report = SubCommand(self._config, "report")

        # フォントファイルチェック
        for chk_dir in (self.config_dir, self.script_dir):
            chk_path = os.path.realpath(os.path.join(chk_dir, self.setting.font_file))
            if os.path.exists(chk_path):
                Config.setting.font_file = chk_path
                break
        if chk_path != Config.setting.font_file:
            logging.critical("The specified font file cannot be found.")
            sys.exit(255)

        # その他/更新
        Config.db.database_file = os.path.realpath(os.path.join(self.config_dir, self.db.database_file))
        Config.setting.work_dir = os.path.realpath(os.path.join(self.script_dir, self.setting.work_dir))
        self.undefined_word = self._config["regulations"].getint("undefined", 2)
        self.format = str()
        self.filename = str()
        self.aggregate_unit = str()
        self.interval = 80
        if self.db.backup_dir:
            self.db.backup_dir = os.path.realpath(os.path.join(self.script_dir, self.db.backup_dir))

        logging.info("setting=%s", vars(self.setting))
        logging.info("search=%s", vars(self.search))
        logging.info("database=%s", vars(self.db))
        logging.info("alias=%s", vars(self.alias))
        logging.info("commandword=%s", vars(self.cw))
        logging.info("dropitems=%s", vars(self.dropitems))

    def word_list(self) -> list:
        """設定されている値、キーワードをリスト化する

        Returns:
            list: リスト化されたキーワード
        """

        words: list = []

        words.append([self.setting.slash_command])
        words.append([self.search.keyword])

        for x in self.cw.__dict__.values():
            words.append([x])

        for k, v in self.alias.__dict__.items():
            if isinstance(v, list):
                words.append([k])
                words.append(v)

        words = list(set(chain.from_iterable(words)))
        words = ["del" if x == "delete" else x for x in words]
        words = [x for x in words if x != ""]

        return words
