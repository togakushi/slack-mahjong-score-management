"""
integrations/protocols.py
"""

from dataclasses import dataclass, field, fields, is_dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path  # noqa: F401

    import pandas as pd  # noqa: F401

    from libs.types import MessageType, StyleOptions


class MessageStatus(StrEnum):
    """メッセージステータス"""

    APPEND = "message_append"
    """新規ポストイベント"""
    CHANGED = "message_changed"
    """編集イベント"""
    DELETED = "message_deleted"
    """削除イベント"""
    DO_NOTHING = "do_nothing"
    """何もしなくてよいイベント"""
    UNDETERMINED = "undetermined"
    """未定義状態"""


class ChannelType(StrEnum):
    """チャンネルタイプ"""

    CHANNEL = "normal"
    """通常チャンネル"""
    PRIVATE = "private"
    """プライベートチャンネル"""
    DIRECT_MESSAGE = "direct_message"
    """ダイレクトメッセージ"""
    SEARCH = "search_api"
    """検索API"""
    UNDETERMINED = "undetermined"
    """未定義状態"""


class CommandType(StrEnum):
    """実行(する/した)サブコマンド"""

    RESULTS = "results"
    """成績サマリ"""
    GRAPH = "graph"
    """グラフ生成"""
    RANKING = "ranking"
    """ランキング"""
    RATING = "rating"
    """レーティング"""
    REPORT = "report"
    """レポート"""
    COMPARISON = "comparison"
    """突合処理"""
    UNKNOWN = "unknown"
    """未定義"""


class ActionStatus(StrEnum):
    """DBに対する操作"""

    CHANGE = "change"
    """insert/updateが実行された"""
    DELETE = "delete"
    """deleteが実行された"""
    NOTHING = "nothing"
    """何もしてない"""


class DataMixin:
    """共通処理"""

    def reset(self) -> None:
        """デフォルト値にリセット"""
        if not is_dataclass(self):
            raise TypeError(f"{self.__class__.__name__} must be a dataclass")

        default = type(self)()
        for f in fields(self):
            setattr(self, f.name, getattr(default, f.name))


@dataclass
class MsgData(DataMixin):
    """ポストされたメッセージデータ"""

    text: str = field(default=str())
    """本文"""
    event_ts: str = field(default="undetermined")
    """イベント発生タイムスタンプ"""
    thread_ts: str = field(default="undetermined")
    """スレッド元タイムスタンプ
    - *0*: スレッドになっていない
    - *undetermined*: 未定義状態
    """
    edited_ts: str = field(default="undetermined")
    """イベント編集タイムスタンプ"""
    channel_id: str = field(default=str())
    """チャンネルID"""
    channel_type: ChannelType = field(default=ChannelType.UNDETERMINED)
    """チャンネルタイプ"""
    user_id: str = field(default=str())
    """ユーザーID"""
    status: MessageStatus = field(default=MessageStatus.UNDETERMINED)
    """イベントステータス"""
    reaction_ok: list = field(default_factory=list)
    reaction_ng: list = field(default_factory=list)
    remarks: list = field(default_factory=list)
    """メモ格納用"""


@dataclass
class PostData(DataMixin):
    """ポストするデータ"""

    headline: dict[str, str] = field(default_factory=dict)
    """ヘッダ文"""
    message: list[tuple["MessageType", "StyleOptions"]] = field(default_factory=list)
    """本文
    識別子(タイトルなど)をキーにした辞書型
    """
    thread: bool = field(default=True)
    """スレッドに返す"""
    ts: str = field(default="undetermined")
    """指定タイムスタンプへの強制リプライ"""
    thread_title: str = field(default="")
    """スレッドに付けるタイトル"""


@dataclass
class StatusData(DataMixin):
    """処理した結果"""

    command_type: CommandType = field(default=CommandType.UNKNOWN)
    """実行(する/した)サブコマンド"""
    command_flg: bool = field(default=False)
    """コマンドとして実行されたかチェック
    - *True*: コマンド実行
    - *False*: キーワード呼び出し
    """
    command_name: str = field(default="")
    """実行したコマンド名"""

    reaction: bool = field(default=False)
    """データステータス状態
    - *True*: 矛盾なくデータを取り込んだ(OK)
    - *False*: 矛盾があったがデータを取り込んだ or データを取り込めなかった(NG)
    """
    action: ActionStatus = field(default=ActionStatus.NOTHING)
    """DBに対する操作"""
    target_ts: list = field(default_factory=list)
    """同じ処理をしたタイムスタンプリスト(1件だけの処理でもセットされる)"""
    rpoint_sum: int = field(default=0)
    """素点合計値格納用"""

    result: bool = field(default=True)
    """メッセージデータに対する処理結果
    - *True*: 目的の処理が達成できた
    - *False*: 何らかの原因で処理が達成できなかった
    """
    message: Any = field(default=None)
    """汎用メッセージ"""
    source: str = field(default="")
    """データ入力元識別子"""


class MessageParserProtocol(Protocol):
    """メッセージ解析クラス"""

    data: MsgData
    """受け取ったメッセージデータ"""
    post: PostData
    """送信する内容"""
    status: StatusData
    """処理した結果"""

    @property
    def in_thread(self) -> bool:
        """スレッド内のメッセージか判定"""

    @property
    def is_command(self) -> bool:
        """コマンドとして実行されたかチェック

        Returns:
            bool: 真偽値
            - *True*: スラッシュコマンド
            - *False*: チャンネル内呼び出しキーワード
        """

    @property
    def is_bot(self) -> bool:
        """botによる操作かチェック

        Returns:
            bool: 真偽値
            - *True*: botが操作
            - *False*: ユーザが操作
        """

    @property
    def keyword(self) -> str:
        """コマンドとして認識している文字列を返す"""

    @property
    def argument(self) -> list:
        """コマンド引数として認識しているオプションを文字列のリストで返す"""

    @property
    def reply_ts(self) -> str:
        """リプライ先のタイムスタンプ"""

    @property
    def check_updatable(self) -> bool:
        """DB更新可能チャンネルか判定"""

    @property
    def ignore_user(self) -> bool:
        """コマンドを拒否するユーザか判定"""

    def set_data(self, data: "MessageType", options: "StyleOptions"):
        """メッセージデータをセット"""

    def get_remarks(self, keyword: str) -> list:
        """本文からメモデータを取り出す"""

    def parser(self, body: Any):
        """メッセージ解析メソッド"""

    def reset(self):
        """状態リセット"""
