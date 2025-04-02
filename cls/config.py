"""
cls/config.py
"""

import configparser
import logging
import os
import sys
from dataclasses import dataclass, field
from itertools import chain


@dataclass
class SettingSection:
    """settingセクション初期値"""
    slash_command: str = "/mahjong"
    thread_report: bool = True
    guest_mark: str = "※"
    reaction_ok: str = "ok"
    reaction_ng: str = "ng"
    font_file: str = "ipaexg.ttf"
    work_dir: str = "work"
    ignore_userid: list = field(default_factory=list)


@dataclass
class SearchSection:
    """searchセクション初期値"""
    keyword: str = "終局"
    channel: str | None = None
    after: int = 7
    wait: int = 180


@dataclass
class DatabaseSection:
    """databaseセクション初期値"""
    database_file: str = "mahjong.db"
    channel_limitations: str = str()
    backup_dir: str | None = None


@dataclass
class MemberSection:
    """memberセクション初期値"""
    registration_limit: int = 255
    character_limit: int = 8
    alias_limit: int = 16
    guest_name: str = "ゲスト"


@dataclass
class TeamSection:
    """teamセクション初期値"""
    registration_limit: int = 255
    character_limit: int = 16
    member_limit: int = 16
    friendly_fire: bool = True


@dataclass
class AliasSection:
    """aliasセクション初期値"""
    results: list = field(default_factory=list)
    graph: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)
    check: list = field(default_factory=list)
    download: list = field(default_factory=list)
    member: list = field(default_factory=list)
    add: list = field(default_factory=list)
    delete: list = field(default_factory=list)


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
class SubCommand:
    """サブコマンドデフォルト値"""
    aggregation_range: str = "当日"
    all_player: bool = False
    daily: bool = True
    fourfold: bool = True
    game_results: str | bool = False
    group_length: int = 0
    guest_skip: bool = True
    guest_skip2: bool = True
    ranked: int = 3
    score_comparisons: bool = False
    statistics: bool = False
    stipulated: int = 0
    stipulated_rate: float = 0.05
    unregistered_replace: bool = True
    verbose: bool = False
    versus_matrix: bool = False


@dataclass
class DropItems:
    """非表示項目リスト"""
    results: list = field(default_factory=list)
    ranking: list = field(default_factory=list)
    report: list = field(default_factory=list)


class Config():
    """コンフィグ解析クラス"""
    def __init__(self, filename: str | None = None) -> None:
        self.setting: SettingSection
        self.search: SearchSection
        self.db: DatabaseSection
        self.member: MemberSection
        self.team: TeamSection
        self.alias: AliasSection
        self.dropitems: DropItems
        self.cw: CommandWord
        self.results: SubCommand
        self.graph: SubCommand
        self.ranking: SubCommand
        self.report: SubCommand
        self.undefined_word: int

        self.config = configparser.ConfigParser()
        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename: str) -> None:
        """設定ファイル読み込み

        Args:
            str: 設定ファイル
        """

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
        self.setting = SettingSection(
            slash_command=self.config["setting"].get("slash_commandname", SettingSection.slash_command),
            thread_report=self.config["setting"].getboolean("thread_report", SettingSection.thread_report),
            guest_mark=self.config["setting"].get("guest_mark", SettingSection.guest_mark),
            reaction_ok=self.config["setting"].get("reaction_ok", SettingSection.reaction_ok),
            reaction_ng=self.config["setting"].get("reaction_ng", SettingSection.reaction_ng),
            font_file=self.config["setting"].get("font_file", SettingSection.font_file),
            work_dir=self.config["setting"].get("work_dir", SettingSection.work_dir),
            ignore_userid=[x.strip() for x in self.config["setting"].get("ignore_userid", "").split(",")],
        )
        self.search = SearchSection(
            keyword=self.config["search"].get("keyword", SearchSection.keyword),
            channel=self.config["search"].get("channel", SearchSection.channel),
            after=self.config["search"].getint("after", SearchSection.after),
            wait=self.config["search"].getint("wait", SearchSection.wait),
        )
        self.db = DatabaseSection(
            database_file=self.config["database"].get("database_file", DatabaseSection.database_file),
            channel_limitations=self.config["database"].get("channel_limitations", DatabaseSection.channel_limitations),
            backup_dir=self.config["database"].get("backup_dir", DatabaseSection.backup_dir),
        )
        self.member = MemberSection(
            registration_limit=self.config["member"].getint("registration_limit", MemberSection.registration_limit),
            character_limit=self.config["member"].getint("character_limit", MemberSection.character_limit),
            alias_limit=self.config["member"].getint("alias_limit", MemberSection.alias_limit),
            guest_name=self.config["member"].get("guest_name", MemberSection.guest_name),
        )
        self.team = TeamSection(
            registration_limit=self.config["team"].getint("registration_limit", TeamSection.registration_limit),
            character_limit=self.config["team"].getint("character_limit", TeamSection.character_limit),
            member_limit=self.config["team"].getint("member_limit", TeamSection.member_limit),
            friendly_fire=self.config["team"].getboolean("friendly_fire", TeamSection.friendly_fire),
        )
        self.alias = AliasSection(
            results=[x.strip() for x in self.config["alias"].get("results", "").split(",")],
            graph=[x.strip() for x in self.config["alias"].get("graph", "").split(",")],
            ranking=[x.strip() for x in self.config["alias"].get("ranking", "").split(",")],
            report=[x.strip() for x in self.config["alias"].get("report", "").split(",")],
            check=[x.strip() for x in self.config["alias"].get("check", "").split(",")],
            download=[x.strip() for x in self.config["alias"].get("download", "").split(",")],
            member=[x.strip() for x in self.config["alias"].get("member", "").split(",")],
            add=[x.strip() for x in self.config["alias"].get("add", "").split(",")],
            delete=[x.strip() for x in self.config["alias"].get("del", "").split(",")],
        )
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
        self.results = self.subcom_default_set("results")
        self.graph = self.subcom_default_set("graph")
        self.ranking = self.subcom_default_set("ranking")
        self.report = self.subcom_default_set("report")

        # その他/更新
        self.db.database_file = os.path.realpath(os.path.join(os.path.dirname(filename), self.db.database_file))
        self.setting.work_dir = os.path.realpath(os.path.join(os.path.dirname(filename), self.setting.work_dir))
        self.setting.font_file = os.path.realpath(os.path.join(os.path.dirname(filename), self.setting.font_file))
        self.undefined_word = self.config["regulations"].getint("undefined", 2)

        logging.info("setting=%s", vars(self.setting))
        logging.info("search=%s", vars(self.search))
        logging.info("database=%s", vars(self.db))
        logging.info("alias=%s", vars(self.alias))
        logging.info("commandword=%s", vars(self.cw))
        logging.info("dropitems=%s", vars(self.dropitems))

    def subcom_default_set(self, section: str) -> SubCommand:
        """設定ファイルのセクションを読み込みインスタンス化して返す

        Args:
            section (str): セクション名

        Returns:
            SubCommand: インスタンス
        """

        default: SubCommand = SubCommand()
        default.aggregation_range = self.config[section].get("aggregation_range", SubCommand.aggregation_range)
        default.all_player = self.config[section].getboolean("all_player", SubCommand.all_player)
        default.daily = self.config[section].getboolean("daily", SubCommand.daily)
        default.fourfold = self.config[section].getboolean("fourfold", SubCommand.fourfold)
        default.game_results = self.config[section].get("game_results", SubCommand.game_results)
        default.group_length = self.config[section].getint("group_length", SubCommand.group_length)
        default.guest_skip = self.config[section].getboolean("guest_skip", SubCommand.guest_skip)
        default.guest_skip2 = self.config[section].getboolean("guest_skip2", SubCommand.guest_skip2)
        default.ranked = self.config[section].getint("ranked", SubCommand.ranked)
        default.score_comparisons = self.config[section].getboolean("score_comparisons", SubCommand.score_comparisons)
        default.statistics = self.config[section].getboolean("statistics", SubCommand.statistics)
        default.stipulated = self.config[section].getint("stipulated", SubCommand.stipulated)
        default.stipulated_rate = self.config[section].getfloat("stipulated_rate", SubCommand.stipulated_rate)
        default.unregistered_replace = self.config[section].getboolean("unregistered_replace", SubCommand.unregistered_replace)
        default.verbose = self.config[section].getboolean("verbose", SubCommand.verbose)
        default.versus_matrix = self.config[section].getboolean("versus_matrix", SubCommand.versus_matrix)

        return (default)

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
