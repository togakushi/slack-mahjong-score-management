"""抽象化基底クラス"""

from abc import ABC, abstractmethod
from typing import Any
from cls.types import MsgDict


class ReactionsInterface(ABC):
    """リアクション操作抽象インターフェース"""
    @abstractmethod
    def status(self, ch=str, ts=str) -> list:
        """botが付けたリアクションの種類を返す

        Args:
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ

        Returns:
            list: リアクション
        """
        return []

    @abstractmethod
    def all_remove(self, delete_list: list, ch: str):
        """すべてのリアクションを削除する

        Args:
            delete_list (list): 削除対象のタイムスタンプ
            ch (str): 対象チャンネルID
        """

    @abstractmethod
    def ok(self, ok_icon: str, ng_icon: str, ch: str, ts: str, reactions_list: list) -> None:
        """OKリアクションを付ける

        Args:
            ok_icon (str): OKリアクション
            ng_icon (str): NGリアクション
            ch (str): チャンネルID
            ts (str): タイムスタンプ
            reactions_list (list): 付与済みリアクションリスト
        """

    @abstractmethod
    def ng(self, ok_icon: str, ng_icon: str, ch: str, ts: str, reactions_list: list) -> None:
        """NGリアクションを付ける

        Args:
            ok_icon (str): OKリアクション
            ng_icon (str): NGリアクション
            ch (str): チャンネルID
            ts (str): タイムスタンプ
            reactions_list (list): 付与済みリアクションリスト
        """


class LookupInterface(ABC):
    """情報取得API操作抽象化ンターフェース"""
    @abstractmethod
    def get_channel_id(self) -> str:
        """チャンネルIDを取得する

        Returns:
            str: チャンネルID
        """
        return ""

    @abstractmethod
    def get_dm_channel_id(self, user_id: str) -> str:
        """DMのチャンネルIDを取得する

        Args:
            user_id (str): DMの相手

        Returns:
            str: チャンネルID
        """
        return ""


class APIInterface(ABC):
    """API抽象化インターフェース"""
    lookup: "LookupInterface"
    reactions: "ReactionsInterface"

    @abstractmethod
    def post_message(self, msg: str, ts=False) -> dict:
        """メッセージをポストする

        Args:
            msg (str): ポストする内容
            ts (bool, optional): スレッドにする

        Returns:
            dict: API response
        """
        return {}

    @abstractmethod
    def post_multi_message(self, msg: dict, ts: bool | None = False, summarize: bool = True):
        """辞書の要素単位でメッセージをポストする

        Args:
            msg (dict): ポストする内容
            ts (bool | None, optional): _description_. Defaults to False.
            summarize (bool, optional): _description_. Defaults to True.
        """

    @abstractmethod
    def post_text(self, event_ts: str, title: str, msg: str) -> dict:
        """コードブロック修飾付きでメッセージをポストする

        Args:
            event_ts (str): スレッドに返す
            title (str): タイトル行
            msg (str): ポストする内容

        Returns:
            dict: API response
        """
        return {}

    @abstractmethod
    def post(self, **kwargs):
        """kwargsの内容でポストのふるまいを変える

        - headline:
        - message:
        - summarize:
        - file_list:
        """

    @abstractmethod
    def fileupload(self, title: str, file: str | bool, ts: str | bool = False):
        """ファイルをアップロードする

        Args:
            title (str): タイトル行
            file (str): アップロードファイルパス
            ts (str | bool, optional): スレッドに返す. Defaults to False.
        """

    @abstractmethod
    def get_conversations(self, ch=str, ts=str) -> dict:
        """スレッド情報の取得

        Args:
            ch (str, optional): チャンネルID. Defaults to None.
            ts (str, optional): メッセージのタイムスタンプ. Defaults to None.

        Returns:
            dict: API response
        """
        return {}


class MessageParserInterface(ABC):
    """メッセージ解析インターフェース"""

    client: Any
    text: str | None
    keyword: str
    argument: list
    channel_id: str | None
    channel_type: str | None
    event_ts: str
    thread_ts: str
    user_id: str
    updatable: bool
    in_thread: bool
    status: str

    @abstractmethod
    def parser(self, _body: dict):
        pass

    @abstractmethod
    def check_updatable(self):
        pass


class NewMsgParserInterface(ABC):
    data: MsgDict

    def __init__(self):
        self.data: MsgDict = MsgDict()

    @abstractmethod
    def parser(self, body: Any):
        pass

    @property
    def in_thread(self) -> bool:
        if self.data["thread_ts"] == "0":
            return False
        elif self.data["event_ts"] == self.data["thread_ts"]:
            return False
        return True

    @property
    def text(self) -> str:
        return self.data.get("text", "")

    @property
    def keyword(self) -> str:
        if (ret := self.data["text"].split()):
            return ret[0]
        return ret

    @property
    def argument(self) -> list:
        if (ret := self.data["text"].split()):
            return ret[1:]
        return ret

    @argument.setter
    def argument(self, value: list) -> None:
        if isinstance(value, license):
            self.argument = value

    @property
    def event_ts(self) -> str:
        return self.data.get("event_ts", "0")

    @event_ts.setter
    def event_ts(self, value: str) -> None:
        self.data["event_ts"] = value

    @property
    def thread_ts(self) -> str:
        return self.data.get("thread_ts", "0")

    @property
    def channel_id(self) -> str:
        return self.data.get("channel_id", "")

    @property
    def channel_type(self) -> str:
        return self.data.get("channel_type", "dummy")

    @property
    def user_id(self) -> str:
        return self.data.get("user_id", "")

    @property
    def status(self) -> str:
        return self.data.get("status", "dummy")
