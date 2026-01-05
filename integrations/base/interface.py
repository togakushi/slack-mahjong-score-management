"""
integrations/base/interface.py
"""

import re
from abc import ABC, abstractmethod
from configparser import ConfigParser
from dataclasses import dataclass, field
from types import NoneType
from typing import TYPE_CHECKING, Any, Generic, Literal, Optional, Type, TypeVar

import pandas as pd

from integrations.protocols import MsgData, PostData, StatusData
from libs.types import MessageTypeDict, StyleOptions

if TYPE_CHECKING:
    from pathlib import Path

    from integrations.protocols import MessageParserProtocol
    from libs.types import MessageType

ConfigT = TypeVar("ConfigT", bound="IntegrationsConfig")
ApiT = TypeVar("ApiT", bound="APIInterface")
FunctionsT = TypeVar("FunctionsT", bound="FunctionsInterface")
ParserT = TypeVar("ParserT", bound="MessageParserInterface")


class AdapterInterface(ABC, Generic[ConfigT, ApiT, FunctionsT, ParserT]):
    """アダプタインターフェース"""

    interface_type: str
    """サービス識別子"""

    conf: ConfigT
    """個別設定データクラス"""
    api: ApiT
    """インターフェース操作APIインスタンス"""
    functions: FunctionsT
    """サービス専用関数インスタンス"""
    parser: Type[ParserT]
    """メッセージパーサクラス"""


@dataclass
class IntegrationsConfig(ABC):
    """個別設定値"""

    _parser: Optional[ConfigParser] = field(default=None)

    # ディスパッチテーブル用
    _command_dispatcher: dict = field(default_factory=dict)
    _keyword_dispatcher: dict = field(default_factory=dict)

    # 共通設定
    main_conf: Optional[ConfigParser] = field(default=None)
    """設定ファイル"""
    channel_config: Optional["Path"] = field(default=None)
    """チャンネル個別設定状況
    - *Path*: チャンネル個別設定ファイルパス
    - *None*: 個別設定を利用していない
    """

    slash_command: str = field(default="")
    """スラッシュコマンド名"""
    badge_degree: bool = field(default=False)
    """プレイしたゲーム数に対して表示される称号
    - *True*: 表示する
    - *False*: 表示しない
    """
    badge_status: bool = field(default=False)
    """勝率に対して付く調子バッジ
    - *True*: 表示する
    - *False*: 表示しない
    """
    badge_grade: bool = field(default=False)
    """段位表示
    - *True*: 表示する
    - *False*: 表示しない
    """

    separate: bool = field(default=False)
    """スコア入力元識別子別集計フラグ
    - *True*: 識別子別に集計
    - *False*: すべて集計
    """
    channel_id: Optional[str] = field(default=None)
    """チャンネルIDを上書きする"""

    plotting_backend: Literal["matplotlib", "plotly"] = field(default="matplotlib")
    """グラフ描写ライブラリ"""

    @property
    def command_dispatcher(self) -> dict:
        """コマンドディスパッチテーブルを辞書で取得

        Returns:
            dict: コマンドディスパッチテーブル
        """

        return self._command_dispatcher

    @property
    def keyword_dispatcher(self) -> dict:
        """キーワードディスパッチテーブルを辞書で取得

        Returns:
            dict: キーワードディスパッチテーブル
        """

        return self._keyword_dispatcher


class FunctionsInterface(ABC):
    """個別関数インターフェース"""

    @abstractmethod
    def post_processing(self, m: "MessageParserProtocol"):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

    @abstractmethod
    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        """スレッド情報の取得

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """
        return {}


class APIInterface(ABC):
    """アダプタAPIインターフェース"""

    @abstractmethod
    def post(self, m: "MessageParserProtocol"):
        """メッセージを出力する

        Args:
            m (MessageParserProtocol): メッセージデータ
        """


class MessageParserDataMixin:
    """メッセージ解析共通処理"""

    data: "MsgData"
    post: "PostData"
    status: "StatusData"

    def reset(self) -> None:
        """初期化"""

        self.data.reset()
        self.post.reset()
        self.status.reset()

    def set_data(
        self,
        title: str,
        data: "MessageType",
        options: StyleOptions,
    ):
        """メッセージデータをセット

        Args:
            title (str): データ識別子
            data (MessageType): 内容
            options (StyleOptions): 表示オプション
        """

        # 空データは登録しない
        if isinstance(data, NoneType) or (isinstance(data, pd.DataFrame) and data.empty):
            return

        msg = MessageTypeDict(
            data=data,
            options=options,
        )
        self.post.message.append({title: msg})

    def get_remarks(self, keyword: str) -> list:
        """textからメモを抽出する

        Args:
            keyword (str): メモ記録キーワード

        Returns:
            list: 結果
        """

        ret: list = []
        if re.match(rf"^{keyword}", self.data.text):  # キーワードが先頭に存在するかチェック
            text = self.data.text.replace(keyword, "").strip().split()
            for name, matter in zip(text[0::2], text[1::2]):
                ret.append([name, matter])

        return ret


class MessageParserInterface(ABC):
    """メッセージ解析インターフェース"""

    data: "MsgData"
    post: "PostData"
    status: "StatusData"

    @abstractmethod
    def parser(self, body: Any):
        """メッセージ解析

        Args:
            body (Any): 解析データ
        """

    @property
    @abstractmethod
    def in_thread(self) -> bool:
        """元メッセージへのリプライとなっているか

        Returns:
            bool: 真偽値
            - *True*: リプライの形（リプライ／スレッドなど）
            - *False*: 通常メッセージ
        """

    @property
    @abstractmethod
    def is_bot(self) -> bool:
        """botのポストかチェック

        Returns:
            bool: 真偽値
            - *True*: botのポスト
            - *False*: ユーザのポスト
        """

    @property
    @abstractmethod
    def check_updatable(self) -> bool:
        """DB操作の許可チェック

        Returns:
            bool: 真偽値
            - *True*: 許可
            - *False*: 禁止
        """

    @property
    @abstractmethod
    def ignore_user(self) -> bool:
        """ignore_useridに存在するユーザかチェック

        Returns:
            bool: 真偽値
            - *True*: 存在する(操作禁止ユーザ)
            - *False*: 存在しない
        """

    @property
    def is_command(self) -> bool:
        """コマンドで実行されているかチェック

        Returns:
            bool: 真偽値
            - *True*: コマンド実行
            - *False*: 非コマンド(キーワード呼び出し)
        """

        return self.status.command_flg

    @property
    def keyword(self) -> str:
        """コマンドとして認識している文字列を返す

        Returns:
            str: コマンド名
        """

        if ret := self.data.text.split():
            return ret[0]
        return self.data.text

    @property
    def argument(self) -> list:
        """コマンド引数として認識している文字列をリストで返す

        Returns:
            list: 引数リスト
        """

        if ret := self.data.text.split():
            return ret[1:]
        return ret

    @property
    def reply_ts(self) -> str:
        """リプライ先のタイムスタンプを取得する

        Returns:
            str: タイムスタンプ
        """

        ret_ts: str = "0"

        # tsが指定されていれば最優先
        if self.post.ts != "undetermined":
            return self.post.ts

        # スレッドに返すか
        if self.post.thread and self.in_thread:  # スレッド内
            if self.data.thread_ts != "undetermined":
                ret_ts = self.data.thread_ts
        elif self.post.thread and not self.in_thread:  # スレッド外
            ret_ts = self.data.event_ts

        return ret_ts
