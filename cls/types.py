"""
cls/types.py
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable, TypeAlias, TypedDict, Union

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime
    from integrations import slack, standard_io, web


AppConfigType: TypeAlias = Union[
    "slack.config.AppConfig",
    "web.config.AppConfig",
    "standard_io.config.AppConfig",
]

AdapterType: TypeAlias = Union[
    "slack.adapter.AdapterInterface",
    "web.adapter.AdapterInterface",
    "standard_io.adapter.AdapterInterface",
]


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
