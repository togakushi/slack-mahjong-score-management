"""
integrations/standard_out/message.py
"""

from pprint import pprint
from typing import cast

from integrations.base.adapter import APIInterface


class StandardOut(APIInterface):
    """メッセージ標準出力クラス"""
    def post_message(self, msg: str, ts=False) -> dict:
        """標準出力

        Args:
            message (str): 本文
            ts (bool): 未使用

        Returns:
            dict: ダミー
        """

        _ = ts
        pprint(msg)

        return {}

    def post_multi_message(self, msg: dict, ts: bool | None = False, summarize: bool = True):
        """標準出力

        Args:
            msg (dict): 本文
            ts (bool | None, optional): 未使用
            summarize (bool, optional): 未使用
        """
        _ = ts
        _ = summarize
        pprint(msg)

    def post_text(self, event_ts: str, title: str, msg: str) -> dict:
        """標準出力

        Args:
            event_ts (str): 未使用
            title (str): タイトル行
            msg (str): 本文

        Returns:
            dict: ダミー
        """

        _ = event_ts
        pprint(title)
        pprint(msg)

        return {}

    def post(self, **kwargs):
        """パラメータの内容によって呼び出すAPIを振り分ける"""

        headline = str(kwargs.get("headline", ""))
        msg = kwargs.get("message")
        file_list = cast(dict, kwargs.get("file_list", {"dummy": ""}))

        # 見出しポスト
        pprint(headline)

        # 本文ポスト
        pprint(msg)

        for x in file_list:
            if (file_path := file_list.get(x)):
                pprint(["file:", x, str(file_path)])

    def fileupload(self, title: str, file: str | bool, ts: str | bool = False):
        """標準出力

        Args:
            title (str): タイトル
            file (str | bool): 保存ファイルパス
            ts (str | bool, optional): 未使用
        """

        _ = ts
        pprint(title)
        pprint(file)

    def reactions_status(self, ch=None, ts=None) -> list:
        _ = ch
        _ = ts
        return []

    def all_reactions_remove(self, delete_list: list):
        _ = delete_list

    def get_channel_id(self):
        pass

    def get_dm_channel_id(self, user_id: str):
        _ = user_id

    def get_conversations(self, ch=None, ts=None) -> dict:
        _ = ch
        _ = ts
        return {}
