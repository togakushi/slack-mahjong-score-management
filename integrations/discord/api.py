"""
integrations/discord/api.py
"""

import asyncio
import sys
import textwrap
from pathlib import PosixPath
from typing import TYPE_CHECKING, Optional, cast

import pandas as pd

import integrations.discord.events.audioop as _audioop
from integrations.base.interface import APIInterface
from libs.types import StyleOptions
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from discord import Message

    from integrations.discord.config import SvcConfig
    from integrations.protocols import MessageParserProtocol


class AdapterAPI(APIInterface):
    """インターフェースAPI操作クラス"""

    def __init__(self, conf: "SvcConfig"):
        super().__init__()

        sys.modules["audioop"] = _audioop
        from discord import File as discord_file
        self.discord_file = discord_file

        self.conf = conf
        """個別設定"""

    def post(self, m: "MessageParserProtocol"):
        """メッセージをポストする（非同期処理ラッパー）

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        asyncio.create_task(self.post_async(m))

    async def post_async(self, m: "MessageParserProtocol"):
        """メッセージをポストする

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        def _header_text(title: str) -> str:
            if not title.isnumeric() and title:  # 数値のキーはヘッダにしない
                return f"**【{title}】**\n"
            return ""

        def _table_data(data: dict) -> list:
            ret_list: list = []
            text_data = iter(data.values())
            # 先頭ブロックの処理(ヘッダ追加)
            v = next(text_data)
            ret_list.append(f"{header}```\n{v}\n```\n" if style.codeblock else f"{header}{v}\n")
            # 残りのブロック
            for v in text_data:
                ret_list.append(f"```\n{v}\n```\n" if style.codeblock else f"```\n{v}\n```\n")
            return ret_list

        discord_message = cast("Message", m.status.message)

        if not m.in_thread:
            m.post.thread = False

        # 見出しポスト
        header_title = ""
        header_text = ""
        header_msg: Optional["Message"] = None

        if m.post.headline:
            header_title, header_text = next(iter(m.post.headline.items()))
            if not all(v["options"].header_hidden for x in m.post.message for _, v in x.items()):
                header_msg = await discord_message.reply(f"{_header_text(header_title)}{header_text.rstrip()}")
                m.post.thread = True

        # 本文
        post_msg: list[str] = []
        style = StyleOptions()
        for data in m.post.message:
            for title, val in data.items():
                msg = val.get("data")
                style = val.get("options", StyleOptions())
                header = ""

                if isinstance(msg, PosixPath) and msg.exists():
                    comment = textwrap.dedent(
                        f"{_header_text(header_title)}{header_text.rstrip()}"
                    ) if style.use_comment else ""
                    file = self.discord_file(
                        str(msg),
                        description=comment,
                    )
                    asyncio.create_task(discord_message.channel.send(file=file))

                if isinstance(msg, str):
                    if style.key_title and (title != header_title):
                        header = _header_text(title)
                    post_msg.append(
                        f"{header}```\n{msg.rstrip()}\n```\n" if style.codeblock else f"{header}{msg.rstrip()}\n"
                    )

                if isinstance(msg, pd.DataFrame):
                    if style.key_title and (title != header_title):
                        header = _header_text(title)
                    match m.status.command_type:
                        case "results":
                            match title:
                                case "通算ポイント" | "ポイント差分":
                                    post_msg.extend(_table_data(converter.df_to_dict(msg, step=40)))
                                case "役満和了" | "卓外ポイント" | "その他":
                                    if "回数" in msg.columns:
                                        post_msg.extend(_table_data(converter.df_to_count(msg, title, 1)))
                                    else:
                                        post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                                case "座席データ":
                                    post_msg.extend(_table_data(converter.df_to_seat_data(msg, 1)))
                                case "戦績":
                                    if "東家 名前" in msg.columns:  # 縦持ちデータ
                                        post_msg.extend(_table_data(converter.df_to_results_details(msg)))
                                    else:
                                        post_msg.extend(_table_data(converter.df_to_results_simple(msg)))
                                case _:
                                    post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                        case "rating":
                            post_msg.extend(_table_data(converter.df_to_dict(msg, step=20)))
                        case "ranking":
                            post_msg.extend(_table_data(converter.df_to_ranking(msg, title, step=30)))

        if style.summarize:
            post_msg = formatter.group_strings(post_msg, limit=1800)

        if header_msg and m.post.thread:
            thread = await header_msg.create_thread(name=header_title)
            for msg in post_msg:
                await thread.send(msg)
        else:
            for msg in post_msg:
                await discord_message.reply(msg)
