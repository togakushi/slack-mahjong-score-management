"""抽象化基底クラス"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


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

    @abstractmethod
    def append(self, icon: str, ch: str, ts: str) -> None:
        """リアクションを付ける

        Args:
            icon (str): リアクションの種類
            ch (str): チャンネルID
            ts (str): タイムスタンプ
        """

    @abstractmethod
    def remove(self, icon: str, ch: str, ts: str) -> None:
        """リアクションを外す

        Args:
            icon (str): リアクションの種類
            ch (str): チャンネルID
            ts (str): タイムスタンプ
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
    def post_message(self, m: "MessageParserInterface") -> dict:
        """メッセージをポストする

        Args:
            kwargs (dict): パラメータ
                - **thread** (bool): スレッドにポストするか
                - **msg** (str): ポストするメッセージ
                - **channel_id** (str): ポストするチャンネル
                - **event_ts** (str): リプライ先のタイムスタンプ
                - **thread_ts** (str): リプライ先のタイムスタンプ(スレッド)

        Returns:
            dict: API response
        """
        return {}

    @abstractmethod
    def post_multi_message(self, m: "MessageParserInterface"):
        """辞書の要素単位でメッセージをポストする"""

    @abstractmethod
    def post_text(self, m: "MessageParserInterface") -> dict:
        """コードブロック修飾付きでメッセージをポストする

        Returns:
            dict: API response
        """
        return {}

    @abstractmethod
    def post(self, m: "MessageParserInterface"):
        """メッセージデータの内容でポストのふるまいを変える"""

    @abstractmethod
    def fileupload(self, m: "MessageParserInterface"):
        """ファイルをアップロードする

        Args:
            m (MessageParserInterface): メッセージデータ
        """

    @abstractmethod
    def get_conversations(self, m: "MessageParserInterface") -> dict:
        """スレッド情報の取得

        Returns:
            dict: API response
        """
        return {}


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


class MessageParserInterface(ABC):
    """メッセージ解析インターフェース"""

    def __init__(self):
        self.data = MsgData()
        self.post = PostData()

    @abstractmethod
    def parser(self, body: Any):
        pass

    @property
    @abstractmethod
    def check_updatable(self) -> bool:
        pass

    @property
    def in_thread(self) -> bool:
        if self.data.thread_ts == "0":
            return False
        elif self.data.event_ts == self.data.thread_ts:
            return False
        return True

    @property
    def keyword(self) -> str:
        if (ret := self.data.text.split()):
            return ret[0]
        return self.data.text

    @property
    def argument(self) -> list:
        if (ret := self.data.text.split()):
            return ret[1:]
        return ret

    def get_score(self, keyword: str) -> dict:
        """textからスコアを抽出する

        Args:
            keyword (str): 成績報告キーワード

        Returns:
            dict: 結果
        """

        text = self.data.text
        ret: dict = {}

        # 記号を置換
        replace_chr = [
            (chr(0xff0b), "+"),  # 全角プラス符号
            (chr(0x2212), "-"),  # 全角マイナス符号
            (chr(0xff08), "("),  # 全角丸括弧
            (chr(0xff09), ")"),  # 全角丸括弧
            (chr(0x2017), "_"),  # DOUBLE LOW LINE(半角)
        ]
        for z, h in replace_chr:
            text = text.replace(z, h)

        text = "".join(text.split())  # 改行削除

        # パターンマッチング
        pattern1 = re.compile(
            rf"^({keyword})" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
        )
        pattern2 = re.compile(
            r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})$"
        )
        pattern3 = re.compile(
            rf"^({keyword})\((.+?)\)" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + r"$"
        )
        pattern4 = re.compile(
            r"^" + r"([^0-9()+-]+)([0-9+-]+)" * 4 + rf"({keyword})\((.+?)\)$"
        )

        # 情報取り出し
        position: dict[str, int] = {}
        match text:
            case text if pattern1.findall(text):
                msg = pattern1.findall(text)[0]
                position = {
                    "p1_name": 1, "p1_str": 2,
                    "p2_name": 3, "p2_str": 4,
                    "p3_name": 5, "p3_str": 6,
                    "p4_name": 7, "p4_str": 8,
                }
                comment = None
            case text if pattern2.findall(text):
                msg = pattern2.findall(text)[0]
                position = {
                    "p1_name": 0, "p1_str": 1,
                    "p2_name": 2, "p2_str": 3,
                    "p3_name": 4, "p3_str": 5,
                    "p4_name": 6, "p4_str": 7,
                }
                comment = None
            case text if pattern3.findall(text):
                msg = pattern3.findall(text)[0]
                position = {
                    "p1_name": 2, "p1_str": 3,
                    "p2_name": 4, "p2_str": 5,
                    "p3_name": 6, "p3_str": 7,
                    "p4_name": 8, "p4_str": 9,
                }
                comment = str(msg[1])
            case text if pattern4.findall(text):
                msg = pattern4.findall(text)[0]
                position = {
                    "p1_name": 0, "p1_str": 1,
                    "p2_name": 2, "p2_str": 3,
                    "p3_name": 4, "p3_str": 5,
                    "p4_name": 6, "p4_str": 7,
                }
                comment = str(msg[9])
            case _:
                return ret

        for k, p in position.items():
            ret.update({k: str(msg[p])})

        ret.update(comment=comment)
        ret.update(ts=self.data.event_ts)

        return ret

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
