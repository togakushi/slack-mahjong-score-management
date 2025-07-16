"""
cls/types.py
"""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Callable, Literal, TypedDict, Union

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


class RemarkDict(TypedDict):
    """メモ格納用辞書"""
    thread_ts: str
    """ゲーム終了時間"""
    event_ts: str
    """メモ記録時間"""
    name: str
    matter: str


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


class DateRangeSpec(TypedDict):
    """日付範囲変換キーワード用辞書"""
    keyword: list[str]
    range: Callable[[datetime], list[datetime]]


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


# CommandParser用
CommandResult = Mapping[str, Union[str, int, bool, tuple[str, ...]]]
CommandAction = Callable[[Union[str, tuple[str, ...]]], CommandResult]


class CommandSpec(TypedDict, total=False):
    """コマンドマッピング"""
    match: list[str]
    action: CommandAction
    type: Literal["int", "str", "sql", "filename"]
