"""
integrations/standard_io/adapter.py
"""

import textwrap

import pandas as pd

from integrations.base import interface
from integrations.standard_io import functions
from libs.utils import formatter


class DummyReactionsInterface(interface.ReactionsInterface):
    """ダミークラス"""

    def status(self, ch=str, ts=str, ok=str, ng=str) -> dict[str, list]:
        """abstractmethod dummy"""

        _ = (ch, ts, ok, ng)
        return {"ok": [], "ng": []}

    def append(self, icon: str, ch: str, ts: str) -> None:
        """abstractmethod dummy"""

        _ = (icon, ch, ts)

    def remove(self, icon: str, ch: str, ts: str) -> None:
        """abstractmethod dummy"""

        _ = (icon, ch, ts)


class StandardIO(interface.APIInterface):
    """メッセージ標準出力クラス"""

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

    def post(self, m: interface.MessageParserProtocol):
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
        if m.post.message:
            for title, msg in m.post.message.items():
                if not title.isnumeric() and title and m.post.key_header:
                    print(f"【{title}】")

                if isinstance(msg, str):
                    print(self._text_formatter(msg))

                if isinstance(msg, pd.DataFrame):
                    fmt = formatter.floatfmt_adjust(msg, index=False)
                    disp = msg.to_markdown(index=False, tablefmt="simple_outline", floatfmt=fmt).replace(" nan ", "-----")
                    match title:
                        case "座席データ":
                            disp = disp.replace("0.00", "-.--")
                    print(disp)
                print("")


class AdapterInterface:
    """standard input/output interface"""

    interface_type = "standard_io"
    plotting_backend = "matplotlib"

    def __init__(self):
        self.api = StandardIO()
        self.functions = functions.StandardIOFunctions()
        self.reactions = DummyReactionsInterface()
