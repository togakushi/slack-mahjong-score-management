"""
integrations/discord/events/handler.py
"""

import logging
import os
import sys
from typing import TYPE_CHECKING

import integrations.discord.events.audioop as _audioop
import libs.dispatcher
from libs.types import MessageStatus

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter


def main(adapter: "ServiceAdapter"):
    """メイン処理

    Args:
        adapter (ServiceAdapter): アダプタインターフェース

    Raises:
        ModuleNotFoundError: ライブラリ未インストール
    """

    try:
        sys.modules["audioop"] = _audioop
        import discord
        from discord.ext import commands
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(err.msg) from None

    # ログレベル変更
    for name in logging.Logger.manager.loggerDict:
        if name.startswith(("discord_", "discord")):
            logging.getLogger(name).setLevel(logging.WARNING)

    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    bot = commands.Bot(intents=intents)
    adapter.api.bot = bot

    @bot.event
    async def on_ready():
        logging.info("login: %s", bot.user)
        adapter.conf.bot_name = bot.user

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        adapter.api.response = message

        m = adapter.parser()
        m.data.status = MessageStatus.APPEND
        m.parser(message)

        libs.dispatcher.by_keyword(m)

    @bot.event
    async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
        channel = bot.get_channel(payload.channel_id)
        if channel is None or not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return  # メッセージが既に削除されていた場合
        except discord.Forbidden:
            return  # 権限不足
        except discord.HTTPException:
            return  # Discord API 側の一時的エラーなど

        assert isinstance(message, discord.Message)

        if message.author.bot:
            return

        adapter.api.response = message

        m = adapter.parser()
        m.data.status = MessageStatus.CHANGED
        m.parser(message)

        libs.dispatcher.by_keyword(m)

    @bot.event
    async def on_message_delete(message: discord.Message):
        if message.author.bot:
            return

        adapter.api.response = message

        m = adapter.parser()
        m.data.status = MessageStatus.DELETED
        m.parser(message)

        libs.dispatcher.by_keyword(m)

    @bot.slash_command(name=adapter.conf.slash_command)
    async def slash_command(ctx: discord.ApplicationContext, command: str):
        adapter.api.response = ctx

        m = adapter.parser()
        m.status.command_flg = True
        m.data.text = command
        m.data.status = MessageStatus.APPEND
        m.data.thread_ts = "0"

        libs.dispatcher.by_keyword(m)

    bot.run(token=os.environ["DISCORD_TOKEN"])
