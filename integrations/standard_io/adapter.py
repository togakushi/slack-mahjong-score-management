"""
integrations/standard_io/message.py
"""

import textwrap

import pandas as pd

from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)
from integrations.protocols import MessageParserProtocol
from libs.utils import formatter


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
            line = line.replace("```", "")
            line = textwrap.dedent(line)
            if line:
                ret += f"{line}\n"
        return ret.strip()

    def post(self, m: MessageParserProtocol):
        """メッセージ出力

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        # 見出し
        if m.post.headline:
            title, text = next(iter(m.post.headline.items()))
            if text:
                print("=" * 80)
                if not title.isnumeric() and title:
                    print(f"【{title}】")
                print(textwrap.dedent(text).rstrip())
                print("=" * 80)

        # ファイル
        ret_flg: bool = False
        for file_list in m.post.file_list:
            title, file_path = next(iter(file_list.items()))
            if file_path:
                ret_flg = True
                print(f"{title}: {file_path}")
        if ret_flg:
            return

        # 本文
        for title, msg in m.post.message.items():
            if not title.isnumeric() and title and m.post.key_header:
                print(f"【{title}】")

            if isinstance(msg, str):
                print(self._text_formatter(msg))

            if isinstance(msg, pd.DataFrame):
                match m.data.command_type:
                    case "ranking":
                        fmt = formatter.floatfmt_adjust(msg, index=False)
                    case _:
                        fmt = formatter.floatfmt_adjust(msg, index=True)
                print(msg.to_markdown(index=False, tablefmt="simple_outline", floatfmt=fmt).replace("nan", "---"))

            print("")

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """ダミー

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: ダミー
        """

        _ = m
        return {}
