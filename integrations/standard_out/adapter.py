"""
integrations/standard_out/message.py
"""

from pprint import pprint

from integrations.base import MessageParserInterface
from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)


class _ReactionsDummy(ReactionsInterface):
    def status(self, ch=str, ts=str) -> list:
        _ = (ch, ts)
        return []

    def all_remove(self, delete_list: list, ch: str) -> None:
        _ = (delete_list, ch)

    def ok(self, ok_icon: str, ng_icon: str, ch: str, ts: str, reactions_list: list) -> None:
        _ = (ok_icon, ng_icon, ch, ts, reactions_list)

    def ng(self, ok_icon: str, ng_icon: str, ch: str, ts: str, reactions_list: list) -> None:
        _ = (ok_icon, ng_icon, ch, ts, reactions_list)

    def append(self, icon, ch, ts) -> None:
        _ = (icon, ch, ts)

    def remove(self, icon, ch, ts) -> None:
        _ = (icon, ch, ts)


class _LookupDummy(LookupInterface):
    def get_channel_id(self):
        pass

    def get_dm_channel_id(self, user_id: str):
        _ = user_id


class StandardOut(APIInterface):
    """メッセージ標準出力クラス"""
    def __init__(self):
        self.lookup = _LookupDummy()
        self.reactions = _ReactionsDummy()

    def post_message(self, m: MessageParserInterface) -> dict:
        """標準出力"""

        pprint(m.post.message)

        return {}

    def post_multi_message(self, m: MessageParserInterface):
        """標準出力"""

        pprint(m.post.message)

    def post_text(self, m: MessageParserInterface) -> dict:
        """標準出力

        Args:
            title (str): タイトル行
            msg (str): 本文

        Returns:
            dict: ダミー
        """

        pprint(m.post.title)
        pprint(m.post.message)

        return {}

    def post(self, m: MessageParserInterface):
        """パラメータの内容によって呼び出すAPIを振り分ける"""

        pprint(m.post.headline)
        pprint(m.post.message)
        pprint(m.post.file_list)

    def fileupload(self, m: MessageParserInterface):
        """標準出力"""
        pprint(m.post.title)
        pprint(m.post.file_list)

    def get_conversations(self, m: MessageParserInterface) -> dict:
        _ = m
        return {}
