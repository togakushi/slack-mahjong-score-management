"""
integrations/standard_io/adapter.py
"""

import textwrap
from configparser import ConfigParser

import pandas as pd

from integrations import standard_io
from integrations.base import interface
from libs.utils import formatter


class AdapterAPI(interface.APIInterface):
    """インターフェースAPI操作クラス"""

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
            line = line.replace("<@>", "")
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


class ServiceAdapter:
    """standard input/output interface"""

    interface_type = "standard_io"

    def __init__(self, parser: ConfigParser):
        self.conf = standard_io.config.AppConfig(config_file=parser)
        self.api = AdapterAPI()
        self.functions = standard_io.functions.StandardIOFunctions()
        self.parser = standard_io.parser.MessageParser
