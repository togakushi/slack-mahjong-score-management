"""
cls/parser.py
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd
from slack_sdk import WebClient

import libs.global_value as g
from cls.timekit import ExtendedDatetime as ExtDt
from cls.types import CommandSpec
from libs.data import lookup
from libs.utils import textutil


@dataclass
class ParsedCommand:
    """コマンド解析結果"""
    flags: dict[str, Any]
    arguments: list[str]
    unknown: list[str]
    search_range: list["ExtDt"]


CommandsDict = dict[str, CommandSpec]
COMMANDS: CommandsDict = {
    "guest": {
        "match": [r"^ゲストナシ$", r"^ゲストアリ$", r"^ゲスト無効$"],
        "action": lambda w: {
            "ゲストナシ": {"guest_skip": False, "guest_skip2": False, "unregistered_replace": True},
            "ゲストアリ": {"guest_skip": True, "guest_skip2": True, "unregistered_replace": True},
            "ゲスト無効": {"unregistered_replace": False},
        }[w[0] if isinstance(w, tuple) else w],
    },
    "anonymous": {
        "match": [r"^匿名$", r"^anonymous$"],
        "action": lambda w: {"anonymous": True},
    },

    "individual": {
        "match": [r"^個人$", "^個人成績$"],
        "action": lambda w: {"individual": True},
    },
    "team": {
        "match": [r"^チーム$", "^チーム成績$", "^team$"],
        "action": lambda w: {"individual": False},
    },

    "all_player": {
        "match": [r"^全員$", r"^all$"],
        "action": lambda w: {"all_player": True},
    },

    "a": {
        "match": [r"^(チーム同卓アリ|コンビアリ|同士討チ)$"],
        "action": lambda w: {"friendly_fire": True},
    },
    "b": {
        "match": [r"^(チーム同卓ナシ|コンビナシ)$"],
        "action": lambda w: {"friendly_fire": False},
    },
    # --- 動作変更フラグ
    "score_comparisons": {  # 比較
        "match": [r"^比較$", r"^点差$", r"^差分$"],
        "action": lambda w: {"score_comparisons": True},
    },
    "order": {  # 順位出力
        "match": [r"^順位$"],
        "action": lambda w: {"order": True},
    },
    "results": {  # 戦績
        "match": [r"^戦績$"],
        "action": lambda w: {"game_results": True},
    },
    "versus": {  # 対戦結果
        "match": [r"^対戦結果$", r"^対戦$"],
        "action": lambda w: {"versus_matrix": True},
    },
    "statistics": {  # 統計
        "match": [r"^統計$"],
        "action": lambda w: {"statistics": True},
    },
    "rating": {  # レーティング
        "match": [r"^レート$", r"^レーティング$", r"^rate$", r"^ratings?$"],
        "action": lambda w: {"rating": True},
    },
    "verbose": {  # 詳細
        "match": [r"^詳細$", r"^verbose$"],
        "action": lambda w: {"verbose": True},
    },
    # --- 集計条件
    "ranked": {
        "match": [r"^(トップ|上位|top)(\d*)$"],
        "action": lambda w: {"ranked": w},
    },
    "stipulated": {
        "match": [r"^(規定数|規定打数)(\d*)$"],
        "action": lambda w: {"stipulated": w}
    },
    "interval": {
        "match": [r"^(期間|区間|区切リ?|interval)(\d*)$"],
        "action": lambda w: {"interval": w}
    },
    # --- 集約 / 検索条件
    "daily": {
        "match": [r"^daily$", r"^日次$", r"^デイリー$"],
        "action": lambda w: {"collection": "daily"},
    },
    "monthly": {
        "match": [r"^monthly$", r"^月次$", r"^マンスリー$"],
        "action": lambda w: {"collection": "monthly"},
    },
    "yearly": {
        "match": [r"^yearly$", r"^年次$", r"^イヤーリー$"],
        "action": lambda w: {"collection": "yearly"},
    },
    "collection": {
        "match": [r"^全体$"],
        "action": lambda w: {"collection": "all"}
    },
    "comment": {
        "match": [r"^(コメント|comment)(.*)$"],
        "action": lambda w: {"search_word": w},
        "type": "sql",
    },
    "grouping": {
        "match": [r"^(集約)(\d*)$"],
        "action": lambda w: {"group_length": w}
    },
    "rule_version": {
        "match": [r"^(ルール|rule)(.*)$"],
        "action": lambda w: {"rule_version": w},
        "type": "str",
    },
    "most_recent": {
        "match": [r"^(直近)(\d*)$"],
        "action": lambda w: {"target_count": w}
    },
    # --- 出力オプション
    "format": {
        "match": [r"^(csv|text|txt)$"],
        "action": lambda w: {"format": w},
        "type": "str",
    },
    "filename": {
        "match": [r"^(filename:|ファイル名)(.*)$"],
        "action": lambda w: {"filename": w},
        "type": "filename",
    },
}


class CommandParser:
    """引数解析クラス"""

    def __init__(self):
        self.day_format = re.compile(r"^([0-9]{8}|[0-9/.-]{8,10})$")
        """日付文字列判定用正規表現
        - *yyyymmdd*
        - *yyyy/mm/dd*, *yyyy/m/d*
        - *yyyy-mm-dd*, *yyyy-m-d*
        - *yyyy.mm.dd*, *yyyy.m.d*
        """

    @classmethod
    def is_valid_command(cls, word: str) -> bool:
        """引数がコマンド名と一致するか判定する

        Args:
            word (str): チェック文字列

        Returns:
            bool: 真偽
        """

        for cmd in COMMANDS.values():
            for pattern in cmd["match"]:
                m = re.match(pattern, word)
                if m:
                    return True
                m = re.match(pattern, textutil.str_conv(word.lower(), "h2k"))
                if m:
                    return True

        return False

    def analysis_argument(self, argument: list[str]) -> ParsedCommand:
        """コマンドライン引数を解析する

        Args:
            argument (list[str]): 引数

        Returns:
            ParsedCommand: 結果
        """

        ret: dict = {}
        unknown: list = []
        args: list = []
        search_range: list = []

        for keyword in argument:
            check_word = textutil.str_conv(keyword.lower(), "h2k")
            check_word = check_word.replace("無シ", "ナシ").replace("有リ", "アリ")

            if re.match(r"^([0-9]{8}|[0-9/.-]{8,10})$", check_word):
                try_day = pd.to_datetime(check_word, errors="coerce").to_pydatetime()
                if not pd.isna(try_day):
                    search_range.append(ExtDt(try_day))
                    search_range.append(ExtDt(try_day) + {"hour": 23, "minute": 59, "second": 59, "microsecond": 999999})
                continue

            if check_word in ExtDt.valid_keywords():
                search_range.append(check_word)
                continue

            for cmd in COMMANDS.values():
                for pattern in cmd["match"]:
                    m = re.match(pattern, keyword)
                    if m:
                        ret.update(self._parse_match(cmd, m))
                        break
                    m = re.match(pattern, check_word)
                    if m:
                        ret.update(self._parse_match(cmd, m))
                        break
                else:
                    continue
                break
            else:
                unknown.append(keyword)

        return ParsedCommand(flags=ret, arguments=args, unknown=unknown, search_range=search_range)

    def _parse_match(self, cmd: CommandSpec, m: re.Match) -> dict:
        """コマンド名に一致したときの処理

        Args:
            cmd (CommandSpec): コマンドマップ
            m (re.Match): Matchオブジェクト

        Returns:
            dict: 更新用辞書
        """
        ret: dict = {}

        match len(m.groups()):
            case 0:  # 完全一致: ^command$
                ret.update(cmd["action"](m.group()))
            case 1:  # 選択: ^(command1|command2|...)$
                ret.update(cmd["action"](m.groups()[0]))
            case 2:  # 引数あり: ^(command)(\d*)$
                tmp = cmd["action"](m.groups())
                if isinstance(tmp, dict):
                    key = next(iter(tmp.keys()))
                    val = str(tmp[key][1])
                    if "" != val:
                        match cmd.get("type"):
                            case "str":
                                ret.update({key: val})
                            case "sql":
                                ret.update({key: f"%{val}%"})
                            case "filename":
                                if re.search(r"^[\w\-\.]+$", val):
                                    ret.update({key: val})
                            case "int":
                                ret.update({key: int(val)})
                            case _:
                                ret.update({key: int(val) if val.isdigit() else val})

        return ret


class MessageParser:
    """メッセージ解析クラス"""
    client: WebClient = WebClient()
    """slack WebClient オブジェクト"""

    def __init__(self, body: dict | None = None):
        self.channel_id: str | None = str()
        """ポストされたチャンネルのID"""
        self.channel_type: str | None = str()
        """チャンネルタイプ
        - *channel*: 通常チャンネル
        - *group*: プライベートチャンネル
        - *im*: ダイレクトメッセージ
        - *search_messages*: 検索API
        """
        self.user_id: str = str()
        """ポストしたユーザのID"""
        self.text: str | None = str()
        """ポストされた文字列"""
        self.event_ts: str = str()  # テキストのまま処理する
        """タイムスタンプ"""
        self.thread_ts: str = str()  # テキストのまま処理する
        """スレッドになっている場合のスレッド元のタイムスタンプ"""
        self.status: str = str()  # event subtype
        """イベントステータス
        - *message_append*: 新規ポスト
        - *message_changed*: 編集
        - *message_deleted*: 削除
        """
        self.keyword: str = str()
        self.argument: list = []
        self.updatable: bool = bool()
        self.in_thread: bool = bool()

        if isinstance(body, dict):
            self.parser(body)

    def parser(self, _body: dict):
        """postされたメッセージをパースする

        Args:
            _body (dict): postされたデータ
        """

        logging.trace(_body)  # type: ignore

        # 初期値
        self.text = ""
        self.channel_id = ""
        self.user_id = ""
        self.thread_ts = "0"
        self.keyword = ""
        self.argument = []

        if _body.get("command") == g.cfg.setting.slash_command:  # スラッシュコマンド
            _event = _body
            if not self.channel_id:
                if _body.get("channel_name") == "directmessage":
                    self.channel_id = _body.get("channel_id", None)
                else:
                    self.channel_id = lookup.api.get_dm_channel_id(_body.get("user_id", ""))

        if _body.get("container"):  # Homeタブ
            self.user_id = _body["user"].get("id")
            self.channel_id = lookup.api.get_dm_channel_id(self.user_id)
            self.text = "dummy"

        _event = self.get_event_attribute(_body)
        self.user_id = _event.get("user", self.user_id)
        self.event_ts = _event.get("ts", self.event_ts)
        self.thread_ts = _event.get("thread_ts", self.thread_ts)
        self.channel_type = self.get_channel_type(_body)

        # スレッド内のポストか判定
        if float(self.thread_ts):
            self.in_thread = self.event_ts != self.thread_ts
        else:
            self.in_thread = False

        if "text" in _event:
            self.text = _event.get("text")
            if self.text:  # 空文字以外はキーワードと引数に分割
                self.keyword = self.text.split()[0]
                self.argument = self.text.split()[1:]
        else:  # text属性が見つからないときはログに出力
            if not _event.get("text") and not _body.get("type") == "block_actions":
                logging.error("text not found: %s", _body)

        self.check_updatable()
        logging.info("channel_id=%s, channel_type=%s", self.channel_id, self.channel_type)

    def get_event_attribute(self, _body: dict) -> dict:
        """レスポンスからevent属性を探索して返す

        Args:
            _body (dict): レスポンス内容

        Returns:
            dict: event属性
        """

        _event: dict = {}

        if _body.get("command") == g.cfg.setting.slash_command:
            _event = _body

        if _body.get("event"):
            if not self.channel_id:
                if _body.get("channel_name") != "directmessage":
                    self.channel_id = _body["event"].get("channel")
                else:
                    self.channel_id = lookup.api.get_dm_channel_id(_body.get("user_id", ""))

            match _body["event"].get("subtype"):
                case "message_changed":
                    self.status = "message_changed"
                    _event = _body["event"]["message"]
                case "message_deleted":
                    self.status = "message_deleted"
                    _event = _body["event"]["previous_message"]
                case "file_share":
                    self.status = "message_append"
                    _event = _body["event"]
                case None:
                    self.status = "message_append"
                    _event = _body["event"]
                case _:
                    self.status = "message_append"
                    _event = _body["event"]
                    logging.info("unknown subtype: %s", _body)

        return _event

    def get_channel_type(self, _body: dict) -> str | None:
        """レスポンスからchannel_typeを探索して返す

        Args:
            _body (dict): レスポンス内容

        Returns:
            str | None: channel_type
        """

        _channel_type: str | None = None

        if _body.get("command") == g.cfg.setting.slash_command:
            if _body.get("channel_name") == "directmessage":
                _channel_type = "im"
            else:
                _channel_type = "channel"
        else:
            if _body.get("event"):
                _channel_type = _body["event"].get("channel_type")

        return _channel_type

    def check_updatable(self):
        """DB更新可能チャンネルのポストかチェックする"""
        self.updatable = False

        if g.cfg.db.channel_limitations:
            if self.channel_id in g.cfg.db.channel_limitations:
                self.updatable = True
        else:  # リストが空なら全チャンネルが対象
            match self.channel_type:
                case "channel":  # public channel
                    self.updatable = True
                case "group":  # private channel
                    self.updatable = True
                case "im":  # direct message
                    self.updatable = False
                case "search_messages":
                    self.updatable = True
                case _:
                    self.updatable = True
