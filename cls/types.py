"""
cls/types.py
"""

from collections.abc import Mapping
from configparser import ConfigParser
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Literal, TypedDict, Union

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime


class GameInfoDict(TypedDict):
    """ゲーム集計情報格納辞書"""
    game_count: int
    """ゲーム数"""
    first_game: "ExtendedDatetime"
    """記録されている最初のゲーム時間"""
    last_game: "ExtendedDatetime"
    """記録されている最後のゲーム時間"""
    first_comment: str | None
    """記録されている最初のゲームコメント"""
    last_comment: str | None
    """記録されている最後のゲームコメント"""


class TeamDataDict(TypedDict):
    """チーム情報格納辞書"""
    id: int
    team: str
    member: list[str]


class ScoreDataDict(TypedDict, total=False):
    """スコアデータ格納用辞書"""
    ts: str
    p1_name: str
    p1_str: str
    p1_rpoint: int
    p1_point: float
    p1_rank: int
    p2_name: str
    p2_str: str
    p2_rpoint: int
    p2_point: float
    p2_rank: int
    p3_name: str
    p3_str: str
    p3_rpoint: int
    p3_point: float
    p3_rank: int
    p4_name: str
    p4_str: str
    p4_rpoint: int
    p4_point: float
    p4_rank: int
    comment: str | None
    deposit: int
    rpoint_sum: int
    rule_version: str


class ComparisonDict(TypedDict, total=False):
    """メモ突合用辞書"""
    mismatch: str
    """差分"""
    missing: str
    """追加"""
    delete: str
    """削除"""
    remark_mod: str
    """メモの修正(追加/削除)"""
    remark_del: str
    """削除"""
    invalid_score: str
    """素点合計不一致"""
    pending: list[str]
    """保留"""


class SlackSearchData(TypedDict, total=False):
    """slack検索結果格納辞書"""
    text: str
    """検索にヒットした本文の内容"""
    channel_id: str
    """見つけたチャンネルID"""
    user_id: str
    """投稿者のユーザID"""
    event_ts: str | None
    """ポストされた時間"""
    thread_ts: str | None
    """スレッドになっている場合、スレッド元の時間"""
    edited_ts: str | None
    """最後に編集された時間"""
    reaction_ok: list
    """botが付けたOKリアクション"""
    reaction_ng: list
    """botが付けたNGリアクション"""
    in_thread: bool
    """スレッドになっていればTrue(スレッド元は除く)"""
    score: list
    """スコア報告なら結果"""
    remarks: list
    """メモならその内容"""


class DateRangeSpec(TypedDict):
    """日付範囲変換キーワード用辞書"""
    keyword: list[str]
    range: Callable[[Any], list[datetime]]


class RankTableDict(TypedDict):
    """昇段ポイント計算テーブル用辞書"""
    grade: str
    point: list
    acquisition: list
    demote: bool


class GradeTableDict(TypedDict, total=False):
    """段位テーブル用辞書"""
    name: str
    addition_expression: str
    table: list[RankTableDict]


@dataclass
class CommonMethodMixin:
    """データクラス共通メソッド"""
    def initialization(self, section: str | None = None) -> None:
        """設定ファイルから値を取りこみ"""
        _config = getattr(self, "_config")
        assert _config is not None, "config must not be None"

        if section is None:
            section = getattr(self, "section")
        assert section is not None, "section must not be None"

        for x in fields(self):
            if x.type == Union[ConfigParser | None]:
                continue
            if x.type == Union[str | None] and x.name == "section":
                setattr(self, x.name, section)
            elif x.type == bool:
                setattr(self, x.name, _config.getboolean(section, x.name, fallback=x.default))
            elif x.type == str:
                setattr(self, x.name, _config.get(section, x.name, fallback=x.default))
            elif x.type == int:
                setattr(self, x.name, _config.getint(section, x.name, fallback=x.default))
            elif x.type == float:
                setattr(self, x.name, _config.getfloat(section, x.name, fallback=x.default))
            elif x.type == list:
                tmp_list: list = []
                for data in _config.get(section, x.name, fallback="").split(","):
                    tmp_list.extend(data.split())
                if x.name == "delete":
                    for data in _config.get(section, "del", fallback="").split(","):
                        tmp_list.extend(data.split())
                setattr(self, x.name, tmp_list)
            else:
                setattr(self, x.name, _config.get(section, x.name, fallback=x.default))

        # 共通パラメータ初期化
        self.format = str()
        self.filename = str()
        self.aggregate_unit = str()
        self.interval = 80

    def to_dict(self) -> dict:
        """必要なパラメータを辞書型で返す

        Returns:
            dict: 返却値
        """

        ret_dict: dict = asdict(self)
        ret_dict.update(format=getattr(self, "format", ""))
        ret_dict.update(filename=getattr(self, "filename", ""))
        ret_dict.update(interval=getattr(self, "interval", 80))

        drop_keys: list = [
            "_config",
            "section",
            "always_argument",
            "regulations_type2",
            "rank_point",
        ]

        for key in drop_keys:
            if key in ret_dict:
                ret_dict.pop(key)

        return ret_dict

    def get_default(self, attr: str) -> Any:
        """デフォルト値を取得して返す

        Args:
            attr (str): 属性

        Raises:
            AttributeError: 未定義

        Returns:
            Any: デフォルト値
        """

        ret: Any

        for x in fields(self):
            if x.name == attr:
                _config = getattr(self, "_config")
                assert _config is not None, "config must not be None"
                section = getattr(self, "section")
                assert section is not None, "section must not be None"

                if x.type == Union[str | None]:
                    ret = None
                elif x.type == bool:
                    ret = _config.getboolean(section, x.name, fallback=x.default)
                elif x.type == str:
                    ret = _config.get(section, x.name, fallback=x.default)
                elif x.type == int:
                    ret = _config.getint(section, x.name, fallback=x.default)
                elif x.type == float:
                    ret = _config.getfloat(section, x.name, fallback=x.default)
                elif x.type == list:
                    ret = []
                else:
                    ret = _config.get(section, x.name, fallback=x.default)
                return ret

        raise AttributeError(f"{attr} has no default or does not exist.")


@dataclass
class ParsedCommand:
    """コマンド解析結果"""
    flags: dict[str, Any]
    arguments: list[str]
    unknown: list[str]
    search_range: list["ExtendedDatetime"]


# CommandParser用
CommandResult = Mapping[str, Union[str, int, bool, tuple[str, ...]]]
CommandAction = Callable[[Union[str, tuple[str, ...]]], CommandResult]


class CommandSpec(TypedDict, total=False):
    """コマンドマッピング"""
    match: list[str]
    action: CommandAction
    type: Literal["int", "str", "sql", "filename"]
