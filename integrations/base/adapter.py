"""抽象化基底クラス"""

from abc import ABC, abstractmethod


class APIInterface(ABC):
    """API抽象化インターフェース"""

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
