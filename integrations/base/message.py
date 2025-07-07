"""メッセージ抽象化"""

from abc import ABC, abstractmethod


class MessageInterface(ABC):
    """メッセージ抽象化インターフェース"""

    @abstractmethod
    def post_message(self, msg: str, ts=False) -> dict:
        """メッセージをポストする

        Args:
            ts (str): スレッドにする
            msg (str): ポストする内容
        """
        pass

    @abstractmethod
    def post_multi_message(self, msg: dict, ts: bool | None = False, summarize: bool = True):
        pass

    @abstractmethod
    def post_text(self, event_ts: str, title: str, msg: str):
        pass

    @abstractmethod
    def post(self, **kwargs):
        pass

    @abstractmethod
    def fileupload(self, title: str, file: str | bool, ts: str | bool = False):
        """files_upload_v2に渡すパラメータを設定

        Args:
            title (str): タイトル行
            file (str): アップロードファイルパス
            ts (str | bool, optional): スレッドに返す. Defaults to False.
        """
        pass
