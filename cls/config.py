import configparser
import logging
import os
import sys
from dataclasses import dataclass, field


class Config():
    def __init__(self, filename: str = None) -> None:
        self.config = configparser.ConfigParser()
        if filename is not None:
            self.read_file(filename)

    def read_file(self, filename: str) -> None:
        try:
            self.config.read(filename, encoding="utf-8")
            logging.notice(f"config read: {filename} -> {self.config.sections()}")  # type: ignore
        except Exception:
            sys.exit("config read error.")

        # 必須セクションチェック
        for x in ("mahjong", "setting"):
            if x not in self.config.sections():
                sys.exit()

        # オプションセクションチェック
        for x in ("results", "graph", "ranking", "report", "member", "alias", "team", "database", "comment", "help"):
            if x not in self.config.sections():
                self.config.add_section(x)

        @dataclass
        class setting:
            slash_command: str = self.config["setting"].get("slash_commandname", "/mahjong")
            guest_mark: str = self.config["setting"].get("guest_mark", "※")
            reaction_ok: str = self.config["setting"].get("reaction_ok", "ok")
            reaction_ng: str = self.config["setting"].get("reaction_ng", "ng")
            font_file: str = self.config["setting"].get("font_file", "ipaexg.ttf")
            _work_dir: str = self.config["setting"].get("work_dir", "work")
            work_dir: str = str()
            ignore_userid: list = field(default_factory=list)
        self.setting = setting()
        self.setting.ignore_userid = [x.strip() for x in self.config["setting"].get("ignore_userid", "").split(",")]
        self.setting.work_dir = os.path.join(os.path.realpath(os.path.curdir), self.setting._work_dir)

        @dataclass
        class search:
            keyword: str = self.config["search"].get("keyword", "終局")
            channel: str = self.config["search"].get("channel", None)
            after: str = self.config["search"].get("after", None)
        self.search = search()

        @dataclass
        class database:
            database_file: str = self.config["database"].get("database_file", "mahjong.db")
            channel_limitations: str = self.config["database"].get("channel_limitations", "")
            backup_dir: str = self.config["database"].get("backup_dir", None)
        self.db = database()

        @dataclass
        class member:
            registration_limit: int = self.config["member"].getint("registration_limit", 255)
            character_limit: int = self.config["member"].getint("character_limit", 8)
            alias_limit: int = self.config["member"].getint("alias_limit", 16)
            guest_name: str = self.config["member"].get("guest_name", "ゲスト")
        self.member = member()

        @dataclass
        class alias:
            results: list = field(default_factory=list)
            graph: list = field(default_factory=list)
            ranking: list = field(default_factory=list)
            report: list = field(default_factory=list)
            check: list = field(default_factory=list)
            download: list = field(default_factory=list)
            member: list = field(default_factory=list)
            add: list = field(default_factory=list)
            delete: list = field(default_factory=list)
        self.alias = alias()
        self.alias.results = [x.strip() for x in self.config["alias"].get("results", "").split(",")]
        self.alias.graph = [x.strip() for x in self.config["alias"].get("graph", "").split(",")]
        self.alias.ranking = [x.strip() for x in self.config["alias"].get("ranking", "").split(",")]
        self.alias.report = [x.strip() for x in self.config["alias"].get("report", "").split(",")]
        self.alias.check = [x.strip() for x in self.config["alias"].get("check", "").split(",")]
        self.alias.download = [x.strip() for x in self.config["alias"].get("download", "").split(",")]
        self.alias.member = [x.strip() for x in self.config["alias"].get("member", "").split(",")]
        self.alias.add = [x.strip() for x in self.config["alias"].get("add", "").split(",")]
        self.alias.delete = [x.strip() for x in self.config["alias"].get("del", "").split(",")]

        @dataclass
        class team:
            registration_limit: int = self.config["team"].getint("registration_limit", 255)
            character_limit: int = self.config["team"].getint("character_limit", 16)
            member_limit: int = self.config["team"].getint("member_limit", 16)
            friendly_fire: bool = self.config["team"].getboolean("friendly_fire", True)
        self.team = team()

        # チャンネル内呼び出しキーワード
        @dataclass
        class cw:
            help: str = self.config["help"].get("commandword", "ヘルプ")
            results: str = self.config["results"].get("commandword", "麻雀成績")
            graph: str = self.config["graph"].get("commandword", "麻雀グラフ")
            ranking: str = self.config["ranking"].get("commandword", "麻雀ランキング")
            report: str = self.config["report"].get("commandword", "麻雀成績レポート")
            member: str = self.config["member"].get("commandword", "メンバー一覧")
            team: str = self.config["team"].get("commandword", "チーム一覧")
            remarks_word: str = self.config["setting"].get("remarks_word", "麻雀成績メモ")
            check: str = self.config["database"].get("commandword", "麻雀成績チェック")
        self.cw = cw()

        # コマンド
        self.results = self.command_opt("results")
        self.graph = self.command_opt("graph")
        self.ranking = self.command_opt("ranking")
        self.report = self.command_opt("report")

    def command_opt(self, section):
        @dataclass
        class subcommand:
            aggregation_range: str = self.config[section].get("aggregation_range", "当日")
            all_player: bool = self.config[section].getboolean("all_player", False)
            daily: bool = self.config[section].getboolean("daily", True)
            # filename: str = self.config[section].get("filename", True)
            # format: str = self.config[section].get("format", True)
            fourfold: bool = self.config[section].getboolean("fourfold", True)
            game_results: bool = self.config[section].get("game_results", False)
            group_length: int = self.config[section].getint("group_length", 0)
            guest_skip: bool = self.config[section].getboolean("guest_skip", True)
            guest_skip2: bool = self.config[section].getboolean("guest_skip2", True)
            # order: bool = self.config[section].get("order", False)
            # personal: bool = self.config[section].get("personal", False)
            ranked: int = self.config[section].getint("ranked", 3)
            score_comparisons: bool = self.config[section].getboolean("score_comparisons", False)
            # search_word: str = self.config[section].get("guest_skip", True)
            statistics: bool = self.config[section].getboolean("statistics", False)
            stipulated: int = self.config[section].getint("stipulated", 0)
            stipulated_rate: float = self.config[section].getfloat("stipulated_rate", 0.05)
            # target_count: int = self.config[section].get("target_count", 0)
            # team_total: bool = self.config[section].get("team_total", False)
            unregistered_replace: bool = self.config[section].getboolean("unregistered_replace", True)
            verbose: bool = self.config[section].getboolean("verbose", False)
            versus_matrix: bool = self.config[section].getboolean("versus_matrix", False)

        return (subcommand())

    def word_list(self):
        words = []

        words.append([self.setting.slash_command])
        words.append([self.search.keyword])

        for x in self.cw.__dict__.values():
            words.append([x])

        for k, v in self.alias.__dict__.items():
            words.append([k])
            words.append(v)

        words = list(set(sum(words, [])))
        words = ["del" if x == "delete" else x for x in words]
        words = [x for x in words if x != ""]

        return (words)
