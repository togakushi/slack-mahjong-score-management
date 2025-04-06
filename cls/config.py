"""
cls/config.py
"""

import configparser
import logging
import os
import sys
from dataclasses import dataclass, field
from itertools import chain

from cls.subcom import SubCommand
from cls.types import CommonMethodMixin


@dataclass
class MahjongSection(CommonMethodMixin):
    """mahjongセクション初期値"""
    config: configparser.ConfigParser | None = None
    rule_version: str = field(default=str())
    origin_point: int = field(default=250)
    return_point: int = field(default=300)
    rank_point: list = field(default_factory=list)
    ignore_flying: bool = field(default=False)
    draw_split: bool = field(default=False)
    regulations_type2: list = field(default_factory=list)

    def __post_init__(self):
        self.initialization("mahjong")


@dataclass
class SettingSection(CommonMethodMixin):
    """settingセクション初期値"""
    config: configparser.ConfigParser | None = None
    slash_command: str = field(default="/mahjong")
    thread_report: bool = field(default=True)
    guest_mark: str = field(default="※")
    reaction_ok: str = field(default="ok")
    reaction_ng: str = field(default="ng")
    font_file: str = field(default="ipaexg.ttf")
    work_dir: str = field(default="work")
    ignore_userid: list = field(default_factory=list)

    def __post_init__(self):
        self.initialization("setting")


@dataclass
class SearchSection(CommonMethodMixin):
    """searchセクション初期値"""
    config: configparser.ConfigParser | None = None
    keyword: str = field(default="終局")
    channel: str | None = field(default=None)
    after: int = field(default=7)
    wait: int = field(default=180)

    def __post_init__(self):
        self.initialization("search")


@dataclass
class DatabaseSection(CommonMethodMixin):
    """databaseセクション初期値"""
    config: configparser.ConfigParser | None = None
    database_file: str = field(default="mahjong.db")
    channel_limitations: str = field(default=str())
    backup_dir: str | None = field(default=None)

    def __post_init__(self):
        self.initialization("database")


@dataclass
class MemberSection(CommonMethodMixin):
    """memberセクション初期値"""
    config: configparser.ConfigParser | None = None
    registration_limit: int = field(default=255)
    character_limit: int = field(default=8)
    alias_limit: int = field(default=16)
    guest_name: str = field(default="ゲスト")

    def __post_init__(self):
        self.initialization("member")


@dataclass
class TeamSection(CommonMethodMixin):
    """teamセクション初期値"""
    config: configparser.ConfigParser | None = None
    registration_limit: int = field(default=255)
    character_limit: int = field(default=16)
    member_limit: int = field(default=16)
    friendly_fire: bool = field(default=True)

    def __post_init__(self):
        self.initialization("team")


@dataclass
class AliasSection(CommonMethodMixin):
    """aliasセクション初期値"""
    config: configparser.ConfigParser | None = None
    results: list = field(default_factory=list)
    graph: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)
    check: list = field(default_factory=list)
    download: list = field(default_factory=list)
    member: list = field(default_factory=list)
    add: list = field(default_factory=list)
    delete: list = field(default_factory=list)

    def __post_init__(self):
        self.initialization("alias")


@dataclass
class CommentSection(CommonMethodMixin):
    """commentセクション初期値"""
    config: configparser.ConfigParser | None = None
    group_length: int = field(default=0)
    search_word: str = field(default=str())

    def __post_init__(self):
        self.initialization("comment")


@dataclass
class CommandWord:
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


@dataclass
class DropItems:
    """非表示項目リスト"""
    results: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)


class Config():
    """コンフィグ解析クラス"""
    def __init__(self, filename: str | None = None) -> None:
        # コンフィグセクション
        self.mahjong: MahjongSection
        self.setting: SettingSection
        self.search: SearchSection
        self.db: DatabaseSection
        self.member: MemberSection
        self.team: TeamSection
        self.alias: AliasSection
        self.comment: CommentSection
        self.dropitems: DropItems
        self.cw: CommandWord
        # サブコマンド
        self.results: SubCommand
        self.graph: SubCommand
        self.ranking: SubCommand
        self.report: SubCommand
        # 共通パラメータ
        self.format: str
        self.filename: str
        self.interval: int
        self.aggregate_unit: str
        self.undefined_word: int

        self.config = configparser.ConfigParser()
        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename: str) -> None:
        """設定ファイル読み込み

        Args:
            str: 設定ファイル
        """

        config_dir = os.path.dirname(filename)

        try:
            self.config.read(os.path.realpath(filename), encoding="utf-8")
            logging.notice("configfile: %s", os.path.realpath(filename))  # type: ignore
            logging.info("read sections: %s", self.config.sections())
        except Exception as e:
            raise RuntimeError(e) from e

        # 必須セクションチェック
        for x in ("mahjong", "setting"):
            if x not in self.config.sections():
                logging.critical("Required section not found. (%s)", x)
                sys.exit(255)

        # オプションセクションチェック
        for x in ("results", "graph", "ranking", "report", "member", "alias", "team", "database", "comment", "regulations", "help"):
            if x not in self.config.sections():
                self.config.add_section(x)

        # セクション読み込み
        self.mahjong = MahjongSection(self.config)
        self.setting = SettingSection(self.config)
        self.search = SearchSection(self.config)
        self.db = DatabaseSection(self.config)
        self.member = MemberSection(self.config)
        self.team = TeamSection(self.config)
        self.alias = AliasSection(self.config)
        self.comment = CommentSection(self.config)
        self.cw = CommandWord(  # チャンネル内呼び出しキーワード
            help=self.config["help"].get("commandword", CommandWord.help),
            results=self.config["results"].get("commandword", CommandWord.results),
            graph=self.config["graph"].get("commandword", CommandWord.graph),
            ranking=self.config["ranking"].get("commandword", CommandWord.ranking),
            report=self.config["report"].get("commandword", CommandWord.report),
            member=self.config["member"].get("commandword", CommandWord.member),
            team=self.config["team"].get("commandword", CommandWord.team),
            remarks_word=self.config["setting"].get("remarks_word", CommandWord.remarks_word),
            check=self.config["database"].get("commandword", CommandWord.check),
        )
        self.dropitems = DropItems(  # 非表示項目リスト
            results=[x.strip() for x in self.config["results"].get("dropitems", "").split(",")],
            ranking=[x.strip() for x in self.config["ranking"].get("dropitems", "").split(",")],
            report=[x.strip() for x in self.config["report"].get("dropitems", "").split(",")],
        )

        # サブコマンドデフォルト
        self.results = SubCommand(self.config, "results")
        self.graph = SubCommand(self.config, "graph")
        self.ranking = SubCommand(self.config, "ranking")
        self.report = SubCommand(self.config, "report")

        # その他/更新
        self.db.database_file = os.path.realpath(os.path.join(config_dir, self.db.database_file))
        self.setting.work_dir = os.path.realpath(os.path.join(config_dir, self.setting.work_dir))
        self.setting.font_file = os.path.realpath(os.path.join(config_dir, self.setting.font_file))
        self.undefined_word = self.config["regulations"].getint("undefined", 2)
        self.format = str()
        self.filename = str()
        self.aggregate_unit = str()
        self.interval = 80
        if self.db.backup_dir:
            self.db.backup_dir = os.path.realpath(os.path.join(config_dir, self.db.backup_dir))

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
            words.append([k])
            words.append(v)

        words = list(set(chain.from_iterable(words)))
        words = ["del" if x == "delete" else x for x in words]
        words = [x for x in words if x != ""]

        return (words)
