"""
integrations/discord/events/handler.py
"""

from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from integrations.discord.adapter import ServiceAdapter


def main(adapter: "ServiceAdapter"):
    """メイン処理"""

    intents = discord.Intents.default()
    intents.message_content = True

    _ = adapter
