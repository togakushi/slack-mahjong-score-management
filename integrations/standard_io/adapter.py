"""
integrations/standard_io/message.py
"""

from pprint import pprint

from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)
from integrations.protocols import MessageParserProtocol


class _ReactionsDummy(ReactionsInterface):
    def status(self, ch=str, ts=str) -> dict[str, list]:
        _ = (ch, ts)
        return {"ok": [], "ng": []}

    def append(self, icon, ch, ts) -> None:
        _ = (icon, ch, ts)

    def remove(self, icon, ch, ts) -> None:
        _ = (icon, ch, ts)


class _LookupDummy(LookupInterface):
    def get_channel_id(self):
        pass

    def get_dm_channel_id(self, user_id: str):
        _ = user_id


class StandardIO(APIInterface):
    """メッセージ標準出力クラス"""
    def __init__(self):
        self.lookup = _LookupDummy()
        self.reactions = _ReactionsDummy()

    def post_message(self, m: MessageParserProtocol) -> dict:
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        pprint(m.post.message)

        return {}

    def post_multi_message(self, m: MessageParserProtocol):
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        pprint(m.post.message)

    def post_text(self, m: MessageParserProtocol) -> dict:
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: ダミー
        """

        pprint(m.post.title)
        pprint(m.post.message)

        return {}

    def post(self, m: MessageParserProtocol):
        """パラメータの内容によって呼び出すAPIを振り分ける

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        pprint(m.post.headline)
        pprint(m.post.message)
        pprint(m.post.file_list)

    def fileupload(self, m: MessageParserProtocol):
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        pprint(m.post.title)
        pprint(m.post.file_list)

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """ダミー

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: ダミー
        """

        _ = m
        return {}
