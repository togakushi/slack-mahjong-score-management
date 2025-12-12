"""
cls/command.py
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable, Literal, TypedDict, Union

import pandas as pd

from cls.timekit import ExtendedDatetime as ExtDt
from libs.utils import formatter, textutil

CommandResult = Mapping[str, Union[str, int, bool, tuple[str, ...]]]
CommandAction = Callable[[Union[str, tuple[str, ...]]], CommandResult]


class CommandSpec(TypedDict, total=False):
    """コマンドマッピングテーブル"""

    match: list[str]
    action: CommandAction
    type: Literal["int", "str", "sql", "filename"]


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
        "action": lambda _: {"anonymous": True},
    },
    "individual": {
        "match": [r"^個人$", "^個人成績$"],
        "action": lambda _: {"individual": True},
    },
    "team": {
        "match": [r"^チーム$", "^チーム成績$", "^team$"],
        "action": lambda _: {"individual": False},
    },
    "all_player": {
        "match": [r"^全員$", r"^all$"],
        "action": lambda _: {"all_player": True},
    },
    "a": {
        "match": [r"^(チーム同卓アリ|コンビアリ|同士討チ)$"],
        "action": lambda _: {"friendly_fire": True},
    },
    "b": {
        "match": [r"^(チーム同卓ナシ|コンビナシ)$"],
        "action": lambda _: {"friendly_fire": False},
    },
    # --- 動作変更フラグ
    "score_comparisons": {  # 比較
        "match": [r"^比較$", r"^点差$", r"^差分$"],
        "action": lambda _: {"score_comparisons": True},
    },
    "order": {  # 順位出力
        "match": [r"^順位$"],
        "action": lambda _: {"order": True},
    },
    "results": {  # 戦績
        "match": [r"^戦績$"],
        "action": lambda _: {"game_results": True},
    },
    "versus": {  # 対戦結果
        "match": [r"^対戦結果$", r"^対戦$"],
        "action": lambda _: {"versus_matrix": True},
    },
    "statistics": {  # 統計
        "match": [r"^統計$"],
        "action": lambda _: {"statistics": True},
    },
    "rating": {  # レーティング
        "match": [r"^レート$", r"^レーティング$", r"^rate$", r"^ratings?$"],
        "action": lambda _: {"rating": True},
    },
    "verbose": {  # 詳細
        "match": [r"^詳細$", r"^verbose$"],
        "action": lambda _: {"verbose": True},
    },
    # --- 集計条件
    "ranked": {
        "match": [r"^(トップ|上位|top)(\d*)$"],
        "action": lambda w: {"ranked": w},
    },
    "stipulated": {"match": [r"^(規定数|規定打数)(\d*)$"], "action": lambda w: {"stipulated": w}},
    "interval": {"match": [r"^(期間|区間|区切リ?|interval)(\d*)$"], "action": lambda w: {"interval": w}},
    # --- 集約 / 検索条件
    "daily": {
        "match": [r"^daily$", r"^日次$", r"^デイリー$"],
        "action": lambda _: {"collection": "daily"},
    },
    "monthly": {
        "match": [r"^monthly$", r"^月次$", r"^マンスリー$"],
        "action": lambda _: {"collection": "monthly"},
    },
    "yearly": {
        "match": [r"^yearly$", r"^年次$", r"^イヤーリー$"],
        "action": lambda _: {"collection": "yearly"},
    },
    "collection": {"match": [r"^全体$"], "action": lambda _: {"collection": "all"}},
    "comment": {
        "match": [r"^(コメント|comment)(.*)$"],
        "action": lambda w: {"search_word": w},
        "type": "sql",
    },
    "grouping": {"match": [r"^(集約)(\d*)$"], "action": lambda w: {"group_length": w}},
    "rule_version": {
        "match": [r"^(ルール|rule)(.*)$"],
        "action": lambda w: {"rule_version": w, "mixed": False},
        "type": "str",
    },
    "most_recent": {"match": [r"^(直近)(\d*)$"], "action": lambda w: {"target_count": w}},
    "mixed": {
        "match": [r"^横断$", r"^mix$", r"^mixed$"],
        "action": lambda _: {"mixed": True},
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


@dataclass
class ParsedCommand:
    """コマンド解析結果"""

    flags: dict[str, Any]
    """真偽値、引数を持つオプションを格納"""
    arguments: list[str]
    """単独オプションを格納"""
    unknown: list[str]
    """オプションと認識されない文字列を格納（プレイヤー名候補）"""
    search_range: list[ExtDt]
    """検索範囲の日時を格納"""


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
                unknown.append(formatter.name_replace(keyword, add_mark=False, not_replace=True))

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

        def with_arguments(tmp: dict):
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

        match len(m.groups()):
            case 0:  # 完全一致: ^command$
                ret.update(cmd["action"](m.group()))
            case 1:  # 選択: ^(command1|command2|...)$
                ret.update(cmd["action"](m.groups()[0]))
            case 2:  # 引数あり: ^(command)(\d*)$
                tmp = cmd["action"](m.groups())
                if isinstance(tmp, dict):
                    for k, v in tmp.items():
                        if isinstance(v, tuple):  # 引数取り出し&セット
                            with_arguments(tmp)
                        if isinstance(v, bool):  # フラグ上書き
                            ret.update({k: v})

        return ret
