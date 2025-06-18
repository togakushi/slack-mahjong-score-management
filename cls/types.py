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
    score: "ScoreDataDict"
    """スコア報告なら結果"""
    remarks: list
    """メモならその内容"""


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
