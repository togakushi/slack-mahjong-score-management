"""
cls/config.py
"""

import configparser
import logging
import os
import sys
from dataclasses import dataclass, field
from itertools import chain


class Config():
    """コンフィグ解析クラス"""
    def __init__(self, filename: str | None = None) -> None:
        self.setting: dataclass
        self.alias: dataclass
        self.db: dataclass
        self.search: dataclass
        self.member: dataclass
        self.team: dataclass

        self.config = configparser.ConfigParser()
        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename: str) -> None:
        """設定ファイル読み込み

        Args:
            str: 設定ファイルパス
        """

        try:
            self.config.read(filename, encoding="utf-8")
            logging.notice("filename: %s", filename)  # type: ignore
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
        self.setting_section()
        self.search_section()
        self.database_section()
        self.member_section()
        self.team_section()
        self.alias_section()

        @dataclass
        class CommandWord:
            """チャンネル内呼び出しキーワード"""
            help: str = self.config["help"].get("commandword", "ヘルプ")
            results: str = self.config["results"].get("commandword", "麻雀成績")
            graph: str = self.config["graph"].get("commandword", "麻雀グラフ")
            ranking: str = self.config["ranking"].get("commandword", "麻雀ランキング")
            report: str = self.config["report"].get("commandword", "麻雀成績レポート")
            member: str = self.config["member"].get("commandword", "メンバー一覧")
            team: str = self.config["team"].get("commandword", "チーム一覧")
            remarks_word: str = self.config["setting"].get("remarks_word", "麻雀成績メモ")
            check: str = self.config["database"].get("commandword", "麻雀成績チェック")
        self.cw = CommandWord()

        # サブコマンドデフォルト
        self.results = self.command_default("results")
        self.graph = self.command_default("graph")
        self.ranking = self.command_default("ranking")
        self.report = self.command_default("report")

        @dataclass
        class DropItems:
            """非表示項目リスト"""
            results: list = field(default_factory=list)
            ranking: list = field(default_factory=list)
            report: list = field(default_factory=list)
        self.dropitems = DropItems()
        self.dropitems.results = [x.strip() for x in self.config["results"].get("dropitems", "").split(",")]
        self.dropitems.ranking = [x.strip() for x in self.config["ranking"].get("dropitems", "").split(",")]
        self.dropitems.report = [x.strip() for x in self.config["report"].get("dropitems", "").split(",")]

        self.undefined_word: int = self.config["regulations"].getint("undefined", 2)

        logging.info("setting=%s", vars(self.setting))
        logging.info("search=%s", vars(self.search))
        logging.info("database=%s", vars(self.db))
        logging.info("alias=%s", vars(self.alias))
        logging.info("commandword=%s", vars(self.cw))
        logging.info("dropitems=%s", vars(self.dropitems))

    def setting_section(self):
        """settingセクション読み込み"""
        @dataclass
        class Setting:
            """初期化"""
            slash_command: str = self.config["setting"].get("slash_commandname", "/mahjong")
            thread_report: bool = self.config["setting"].getboolean("thread_report", True)
            guest_mark: str = self.config["setting"].get("guest_mark", "※")
            reaction_ok: str = self.config["setting"].get("reaction_ok", "ok")
            reaction_ng: str = self.config["setting"].get("reaction_ng", "ng")
            font_file: str = self.config["setting"].get("font_file", "ipaexg.ttf")
            work_dir: str = self.config["setting"].get("work_dir", "work")
            ignore_userid: list = field(default_factory=list)
        self.setting = Setting()
        self.setting.ignore_userid = [x.strip() for x in self.config["setting"].get("ignore_userid", "").split(",")]
        self.setting.work_dir = os.path.join(os.path.realpath(os.path.curdir), self.setting.work_dir)

    def search_section(self):
        """searchセクション読み込み"""
        @dataclass
        class Search:
            """初期化"""
            keyword: str = self.config["search"].get("keyword", "終局")
            channel: str | None = self.config["search"].get("channel", None)
            after: int = self.config["search"].getint("after", 7)
            wait: int = self.config["search"].getint("wait", 180)
        self.search = Search()

    def database_section(self):
        """databaseセクション読み込み"""
        @dataclass
        class Database:
            """初期化"""
            database_file: str = self.config["database"].get("database_file", "mahjong.db")
            channel_limitations: str = self.config["database"].get("channel_limitations", "")
            backup_dir: str | None = self.config["database"].get("backup_dir", None)
        self.db = Database()

    def member_section(self):
        """memberセクション読み込み"""
        @dataclass
        class Member:
            """初期化"""
            registration_limit: int = self.config["member"].getint("registration_limit", 255)
            character_limit: int = self.config["member"].getint("character_limit", 8)
            alias_limit: int = self.config["member"].getint("alias_limit", 16)
            guest_name: str = self.config["member"].get("guest_name", "ゲスト")
        self.member = Member()

    def team_section(self):
        """teamセクション読み込み"""
        @dataclass
        class Team:
            """初期化"""
            registration_limit: int = self.config["team"].getint("registration_limit", 255)
            character_limit: int = self.config["team"].getint("character_limit", 16)
            member_limit: int = self.config["team"].getint("member_limit", 16)
            friendly_fire: bool = self.config["team"].getboolean("friendly_fire", True)
        self.team = Team()

    def alias_section(self):
        """aliasセクション読み込み"""
        @dataclass
        class Alias:
            """初期化"""
            results: list = field(default_factory=list)
            graph: list = field(default_factory=list)
            ranking: list = field(default_factory=list)
            report: list = field(default_factory=list)
            check: list = field(default_factory=list)
            download: list = field(default_factory=list)
            member: list = field(default_factory=list)
            add: list = field(default_factory=list)
            delete: list = field(default_factory=list)
        self.alias = Alias()
        self.alias.results = [x.strip() for x in self.config["alias"].get("results", "").split(",")]
        self.alias.graph = [x.strip() for x in self.config["alias"].get("graph", "").split(",")]
        self.alias.ranking = [x.strip() for x in self.config["alias"].get("ranking", "").split(",")]
        self.alias.report = [x.strip() for x in self.config["alias"].get("report", "").split(",")]
        self.alias.check = [x.strip() for x in self.config["alias"].get("check", "").split(",")]
        self.alias.download = [x.strip() for x in self.config["alias"].get("download", "").split(",")]
        self.alias.member = [x.strip() for x in self.config["alias"].get("member", "").split(",")]
        self.alias.add = [x.strip() for x in self.config["alias"].get("add", "").split(",")]
        self.alias.delete = [x.strip() for x in self.config["alias"].get("del", "").split(",")]

    def command_default(self, section):
        """設定ファイルのセクションを読み込みインスタンス化して返す

        Args:
            section (str): セクション名

        Returns:
            SubCommand: インスタンス
        """

        @dataclass
        class SubCommand:
            """デフォルト値のセット"""
            aggregation_range: str = self.config[section].get("aggregation_range", "当日")
            all_player: bool = self.config[section].getboolean("all_player", False)
            daily: bool = self.config[section].getboolean("daily", True)
            fourfold: bool = self.config[section].getboolean("fourfold", True)
            game_results: str | bool = self.config[section].get("game_results", False)
            group_length: int = self.config[section].getint("group_length", 0)
            guest_skip: bool = self.config[section].getboolean("guest_skip", True)
            guest_skip2: bool = self.config[section].getboolean("guest_skip2", True)
            ranked: int = self.config[section].getint("ranked", 3)
            score_comparisons: bool = self.config[section].getboolean("score_comparisons", False)
            statistics: bool = self.config[section].getboolean("statistics", False)
            stipulated: int = self.config[section].getint("stipulated", 0)
            stipulated_rate: float = self.config[section].getfloat("stipulated_rate", 0.05)
            unregistered_replace: bool = self.config[section].getboolean("unregistered_replace", True)
            verbose: bool = self.config[section].getboolean("verbose", False)
            versus_matrix: bool = self.config[section].getboolean("versus_matrix", False)

        return (SubCommand())

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
