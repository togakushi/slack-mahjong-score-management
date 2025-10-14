"""
integrations/protocols.py
"""

from dataclasses import dataclass, field, fields, is_dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol

if TYPE_CHECKING:
    from libs.types import MessageType, MessageTypeDict


class DataMixin:
    """共通処理"""

    def reset(self) -> None:
        """初期化"""
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
    channel_type: Literal[
        "channel",
        "group",
        "im",
        "search_messages",
        "undetermined",
    ] = field(default="undetermined")
    """チャンネルタイプ
    - *channel*: 通常チャンネル
    - *group*: プライベートチャンネル
    - *im*: ダイレクトメッセージ
    - *search_messages*: 検索API
    - *undetermined*: 未定義状態
    """
    user_id: str = field(default=str())
    """ユーザーID"""
    status: Literal[
        "message_append",
        "message_changed",
        "message_deleted",
        "undetermined",
    ] = field(default="undetermined")
    """イベントステータス
    - *message_append*: 新規ポスト
    - *message_changed*: 編集
    - *message_deleted*: 削除
    - *undetermined*: 未定義状態
    """
    reaction_ok: list = field(default_factory=list)
    reaction_ng: list = field(default_factory=list)
    remarks: list = field(default_factory=list)
    """メモ格納用"""


@dataclass
class PostData(DataMixin):
    """ポストするデータ"""

    headline: dict[str, str] = field(default_factory=dict)
    """ヘッダ文"""
    order: list[dict[str, "MessageTypeDict"]] = field(default_factory=list)
    """本文
    識別子(タイトルなど)をキーにした辞書型
    """
    summarize: bool = field(default=True)
    """本文が文字列型のとき後続の要素を集約する
    - *True*: 可能な限り複数の要素をひとつにまとめる
    - *False*: 要素単位でデータを処理する
    """
    key_header: bool = field(default=True)
    """辞書のキーを見出しにする"""
    thread: bool = field(default=True)
    """スレッドに返す"""
    ts: str = field(default="undetermined")
    """指定タイムスタンプへの強制リプライ"""


@dataclass
class StatusData(DataMixin):
    """処理した結果"""

    command_type: Literal[
        "results",
        "graph",
        "ranking",
        "rating",
        "report",
        "unknown",
    ] = field(default="unknown")
    """実行(する/した)サブコマンド
    - *results*: 成績サマリ
    - *graph*: グラフ生成
    - *ranking*: ランキング
    - *rating*: レーティング
    - *report*: レポート
    - *unknown*: 未定義
    """

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
    action: Literal["change", "delete", "nothing"] = field(default="nothing")
    """DBに対する操作
    - *change*: insert/updateが実行された
    - *delete*: deleteが実行された
    - *nothing*: 何もしてない
    """
    target_ts: list = field(default_factory=list)
    """同じ処理をしたタイムスタンプリスト(1件だけの処理でもセットされる)"""
    rpoint_sum: int = field(default=0)
    """素点合計値格納用"""

    result: bool = field(default=True)
    """メッセージデータに対する処理結果
    - *True*: 目的の処理が達成できた
    - *False*: 何らかの原因で処理が達成できなかった
    """
    message: str = field(default="")
    """個別メッセージ"""


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
        - *True*: スラッシュコマンド
        - *False*: チャンネル内呼び出しキーワード
        """

    @property
    def is_bot(self) -> bool:
        """botによる操作かチェック
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

    def set_data(
        self,
        title: str,
        data: "MessageType",
        codeblock: bool = False,
        show_index: bool = False,
        use_comment: bool = False,
        heder_hidden: bool = False,
    ):
        """メッセージデータをセット"""

    def get_score(self, keyword: str) -> dict:
        """本文からスコアデータを取り出す"""

    def get_remarks(self, keyword: str) -> list:
        """本文からメモデータを取り出す"""

    def parser(self, body: Any):
        """メッセージ解析メソッド"""
