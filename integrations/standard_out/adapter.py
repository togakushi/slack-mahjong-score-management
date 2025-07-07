"""
integrations/standard_out/message.py
"""

from pprint import pprint
from typing import cast

from integrations.base.adapter import APIInterface


class StandardOut(APIInterface):
    def post_message(self, msg: str, ts=False) -> dict:
        """標準出力

        Args:
            message (str): 出力するメッセージ
            ts (bool): ダミー
        """

        _ = ts
        pprint(msg)

        return {}

    def post_multi_message(self, msg: dict, ts: bool | None = False, summarize: bool = True):
        _ = ts
        _ = summarize
        pprint(msg)

    def post_text(self, event_ts: str, title: str, msg: str) -> dict:
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
        _ = ts
        pprint(title)
        pprint(file)
