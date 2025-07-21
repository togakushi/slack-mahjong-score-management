"""抽象化基底クラス"""

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from integrations.protocols import MsgData, PostData

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol


class ReactionsInterface(ABC):
    """リアクション操作抽象インターフェース"""
    @abstractmethod
    def status(self, ch=str, ts=str) -> dict[str, list]:
        """botが付けたリアクションの種類を返す

        Args:
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ

        Returns:
            dict[str,list]: リアクション
            - **str**: 種類
            - **list**: タイムスタンプ
        """
        return {"ok": [], "ng": []}

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
    def post_message(self, m: "MessageParserProtocol") -> dict:
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
    def post_multi_message(self, m: "MessageParserProtocol"):
        """辞書の要素単位でメッセージをポストする"""

    @abstractmethod
    def post_text(self, m: "MessageParserProtocol") -> dict:
        """コードブロック修飾付きでメッセージをポストする

        Returns:
            dict: API response
        """
        return {}

    @abstractmethod
    def post(self, m: "MessageParserProtocol"):
        """メッセージデータの内容でポストのふるまいを変える"""

    @abstractmethod
    def fileupload(self, m: "MessageParserProtocol"):
        """ファイルをアップロードする

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

    @abstractmethod
    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        """スレッド情報の取得

        Returns:
            dict: API response
        """
        return {}


class MessageParserDataMixin:
    """メッセージ解析共通処理"""
    def __init__(self, reaction_ok: str, reaction_ng: str):
        self.data = MsgData()
        self.post = PostData()
        self.reaction_ok = reaction_ok
        self.reaction_ng = reaction_ng

    @property
    def in_thread(self) -> bool:
        """スレッド内のメッセージか判定"""
        if self.data.thread_ts == "0":
            return False
        elif self.data.event_ts == self.data.thread_ts:
            return False
        return True

    @property
    def keyword(self) -> str:
        """コマンドとして認識している文字列を返す

        Returns:
            str: コマンド名
        """

        if (ret := self.data.text.split()):
            return ret[0]
        return self.data.text

    @property
    def argument(self) -> list:
        """コマンド引数として認識している文字列をリストで返す

        Returns:
            list: 引数リスト
        """

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


class MessageParserInterface(ABC):
    """メッセージ解析インターフェース"""
    @abstractmethod
    def parser(self, body: Any):
        """メッセージ解析

        Args:
            body (Any): 解析データ
        """

    @property
    @abstractmethod
    def check_updatable(self) -> bool:
        """DB操作の許可チェック

        Returns:
            bool: 真偽値
            - **True** : 許可
            - **False** : 禁止
        """
