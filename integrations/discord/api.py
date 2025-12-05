"""
integrations/discord/api.py
"""

import asyncio
import sys
import textwrap
from pathlib import PosixPath
from typing import TYPE_CHECKING, Optional, Union, cast

import pandas as pd
from table2ascii import PresetStyle, table2ascii

import integrations.discord.events.audioop as _audioop
from cls.timekit import ExtendedDatetime as ExtDt
from integrations.base.interface import APIInterface
from libs.types import StyleOptions
from libs.utils import converter, formatter, textutil

sys.modules["audioop"] = _audioop

if TYPE_CHECKING:
    from discord import ApplicationContext, Bot, Message

    from integrations.protocols import MessageParserProtocol


class AdapterAPI(APIInterface):
    """インターフェースAPI操作クラス"""

    bot: "Bot"

    def __init__(self):
        super().__init__()

        from discord import File as discord_file

        self.discord_file = discord_file

        # discord object
        self.response: Union["Message", "ApplicationContext"]

    def post(self, m: "MessageParserProtocol"):
        """メッセージをポストする（非同期処理ラッパー）

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        if m.status.command_flg:
            asyncio.create_task(self.command_respond(m))
        else:
            asyncio.create_task(self.post_async(m))

    async def post_async(self, m: "MessageParserProtocol"):
        """メッセージをポストする

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        self.response = cast("Message", self.response)

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

        if not m.in_thread:
            m.post.thread = False

        # 見出しポスト
        header_title = ""
        header_text = ""
        header_msg: Optional["Message"] = None

        if m.post.headline:
            header_title, header_text = next(iter(m.post.headline.items()))
            if not m.post.message:
                header_msg = await self.response.reply(f"{_header_text(header_title)}{header_text.rstrip()}")
                m.post.thread = True
            elif not all(v["options"].header_hidden for x in m.post.message for _, v in x.items()):
                header_msg = await self.response.reply(f"{_header_text(header_title)}{header_text.rstrip()}")
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
                    comment = (
                        textwrap.dedent(f"{_header_text(header_title)}{header_text.rstrip()}")
                        if style.use_comment
                        else ""
                    )
                    file = self.discord_file(
                        str(msg),
                        description=comment,
                    )
                    asyncio.create_task(self.response.channel.send(file=file))

                if isinstance(msg, str):
                    if style.key_title and (title != header_title):
                        header = _header_text(title)

                    message_text = msg.rstrip().replace("<@>", f"<@{self.response.author.id}>")
                    post_msg.append(
                        f"{header}```\n{message_text}\n```\n" if style.codeblock else f"{header}{message_text}\n"
                    )

                if isinstance(msg, pd.DataFrame):
                    if style.key_title and (title != header_title):
                        header = _header_text(title)
                    match m.status.command_type:
                        case "results":
                            match title:
                                case "通算ポイント" | "ポイント差分":
                                    post_msg.extend(_table_data(converter.df_to_text_table(msg, step=40)))
                                case "役満和了" | "卓外清算" | "その他":
                                    if "回数" in msg.columns:
                                        post_msg.extend(_table_data(converter.df_to_count(msg, title, 1)))
                                    else:
                                        post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                                case "成績詳細比較":
                                    post_msg.extend(_table_data(converter.df_to_text_table2(msg, style, 2000)))
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
                            post_msg.extend(_table_data(converter.df_to_text_table(msg, step=20)))
                        case "ranking":
                            post_msg.extend(_table_data(converter.df_to_ranking(msg, title, step=0)))

        if style.summarize:
            if m.status.command_type == "ranking":
                post_msg = textutil.split_text_blocks("".join(post_msg), 1900)
            else:
                post_msg = formatter.group_strings(post_msg, limit=1800)

        if header_msg and m.post.thread:
            date_suffix = ExtDt(float(m.data.event_ts)).format("ymdhm", delimiter="slash")
            thread = await header_msg.create_thread(name=f"{header_title} - {date_suffix}")
            for msg in post_msg:
                await thread.send(msg)
        else:
            for msg in post_msg:
                await self.response.reply(msg)

    async def command_respond(self, m: "MessageParserProtocol"):
        """スラッシュコマンド応答

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        self.response = cast("ApplicationContext", self.response)

        style = StyleOptions()
        for data in m.post.message:
            for _, val in data.items():
                msg = val.get("data")
                style = val.get("options", StyleOptions())

            if isinstance(msg, PosixPath) and msg.exists():
                file = self.discord_file(str(msg))
                await self.response.send(file=file)

            if isinstance(msg, str):
                if style.codeblock:
                    msg = f"```\n{msg}\n```"
                await self.response.respond(msg)

            if isinstance(msg, pd.DataFrame):
                output = table2ascii(
                    header=msg.columns.to_list(),
                    body=msg.to_dict(orient="split")["data"],
                    style=PresetStyle.ascii_borderless,
                )
                await self.response.respond(f"```\n{output}\n```")
