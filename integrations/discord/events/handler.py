"""
integrations/discord/events/handler.py
"""

import logging
import os
import sys
from typing import TYPE_CHECKING

import integrations.discord.events.audioop as _audioop
import libs.dispatcher

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter


def main(adapter: "ServiceAdapter"):
    """メイン処理"""

    sys.modules["audioop"] = _audioop

    import discord

    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Bot(intents=intents)

    @bot.event
    async def on_ready():
        logging.info("login: %s", bot.user)

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        m = adapter.parser()
        m.reset()
        m.parser(message)
        libs.dispatcher.by_keyword(m)

    bot.run(token=os.environ["DISCORD_TOKEN"])
