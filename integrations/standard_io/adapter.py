"""
integrations/standard_io/message.py
"""

import textwrap
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

    def _text_formatter(self, text: str) -> str:
        """テキスト整形

        Args:
            text (str): 対象テキスト

        Returns:
            str: 整形済みテキスト
        """

        ret: str = ""
        for line in text.splitlines():
            line = line.replace("*【", "【")
            line = line.replace("】*", "】")
            line = line.replace("```", "")
            line = textwrap.dedent(line)
            if line:
                ret += f"{line}\n"
        return ret.strip()

    def post_message(self, m: MessageParserProtocol) -> dict:
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        print("=" * 80)
        print(self._text_formatter(m.post.message))
        print("=" * 80)
        print("\n")

        return {}

    def post_multi_message(self, m: MessageParserProtocol):
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        self.post(m)

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

        if self.fileupload(m):  # ファイル生成
            return

        if m.post.headline:  # 見出し
            print("=" * 80)
            print(self._text_formatter(m.post.headline))
            print("=" * 80)
            print("\n")

        if m.post.message:  # 本文
            if isinstance(m.post.message, dict):
                for _, text in m.post.message.items():
                    print(self._text_formatter(text))
                    print("\n")
        else:
            print(self._text_formatter(m.post.message))

    def fileupload(self, m: MessageParserProtocol) -> bool:
        """標準出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        ret_flg: bool = False
        for file_list in m.post.file_list:
            title, path = next(iter(file_list.items()))
            if not path:
                continue
            ret_flg = True
            print(f"{title}: {path}")

        return ret_flg

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """ダミー

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: ダミー
        """

        _ = m
        return {}
