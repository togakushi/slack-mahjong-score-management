"""
integrations/protocols.py
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass
class MsgData:
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
    channel_type: Literal["channel", "group", "im", "search_messages", "undetermined"] = field(default="undetermined")
    """チャンネルタイプ
    - *channel*: 通常チャンネル
    - *group*: プライベートチャンネル
    - *im*: ダイレクトメッセージ
    - *search_messages*: 検索API
    - *undetermined*: 未定義状態
    """
    user_id: str = field(default=str())
    """ユーザーID"""
    status: Literal["message_append", "message_changed", "message_deleted", "undetermined"] = field(default="undetermined")
    """イベントステータス
    - *message_append*: 新規ポスト
    - *message_changed*: 編集
    - *message_deleted*: 削除
    - *undetermined*: 未定義状態
    """
    reaction_ok: list = field(default_factory=list)
    reaction_ng: list = field(default_factory=list)


@dataclass
class PostData:
    """ポストするデータ"""
    title: str = field(default=str())
    headline: str = field(default=str())
    message: str | dict[str, str] = field(default=str())
    """本文"""
    message_type: str = field(default="invalid_argument")
    """ランダムリプライが返すメッセージ種類"""
    summarize: bool = field(default=True)
    thread: bool = field(default=False)
    """スレッドに返す"""
    file_list: list[dict[str, str]] = field(default_factory=list)
    ts: str = field(default="undetermined")
    """指定タイムスタンプへのリプライ"""
    rpoint_sum: int = field(default=0)


@runtime_checkable
class MessageParserProtocol(Protocol):
    """メッセージ解析クラス"""
    data: MsgData
    """受け取ったメッセージデータ"""
    post: PostData
    """送信する内容"""

    @property
    def in_thread(self) -> bool:
        """スレッド内のメッセージか判定"""

    @property
    def keyword(self) -> str:
        """コマンドとして認識している文字列を返す"""

    @property
    def argument(self) -> list:
        """コマンド引数として認識しているオプションを文字列のリストで返す"""

    def get_score(self, keyword: str) -> dict:
        """本文からスコアデータを取り出す"""

    def get_remarks(self, keyword: str) -> list:
        """本文からメモデータを取り出す"""

    def parser(self, body: Any):
        """メッセージ解析メソッド"""

    @property
    def check_updatable(self) -> bool:
        """DB更新可能チャンネルか判定"""
