"""
cls/types.py
"""

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Optional, TypedDict

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
    first_comment: Optional[str]
    """記録されている最初のゲームコメント"""
    last_comment: Optional[str]
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
    """段位名称"""
    point: list
    """初期ポイントと昇段に必要なポイント"""
    acquisition: list
    """獲得ポイント(順位)"""
    demote: bool
    """降格フラグ
    - *True*: 降格する(省略時デフォルト)
    - *False*: 降格しない
    """


class GradeTableDict(TypedDict, total=False):
    """段位テーブル用辞書"""

    name: str
    """識別名"""
    addition_expression: str
    """素点評価式(昇段ポイントに加算)"""
    table: list[RankTableDict]
    """昇段ポイント計算テーブル"""
