"""
integrations/protocols.py
"""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass
class MsgData:
    """ポストされたメッセージデータ"""
    text: str = field(default=str())
    event_ts: str = field(default="undetermined")
    thread_ts: str = field(default="undetermined")
    """スレッド元タイムスタンプ
    - *0*: スレッドになっていない
    - *undetermined*: 未定義状態
    """
    edited_ts: str = field(default="undetermined")
    channel_id: str = field(default=str())
    channel_type: Literal["channel", "group", "im", "search_messages", "undetermined"] = field(default="undetermined")
    """チャンネルタイプ
    - *channel*: 通常チャンネル
    - *group*: プライベートチャンネル
    - *im*: ダイレクトメッセージ
    - *search_messages*: 検索API
    - *undetermined*: 未定義状態
    """
    user_id: str = field(default=str())
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
    message_type: str = field(default="invalid_argument")
    summarize: bool = field(default=True)
    thread: bool = field(default=False)
    file_list: list[dict[str, str]] = field(default_factory=list)
    ts: str = field(default="undetermined")
    rpoint_sum: int = field(default=0)


class MessageParserProtocol(Protocol):
    data: MsgData
    post: PostData

    @property
    def in_thread(self) -> bool:
        ...

    @property
    def keyword(self) -> str:
        ...

    @property
    def argument(self) -> list:
        ...

    def get_score(self, keyword: str) -> dict:
        ...

    def get_remarks(self, keyword: str) -> list:
        ...

    def parser(self, body: Any):
        ...

    @property
    def check_updatable(self) -> bool:
        ...
