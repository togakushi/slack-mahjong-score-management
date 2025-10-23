"""
integrations/discord/functions.py
"""

import asyncio
from typing import TYPE_CHECKING, cast

from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from discord import ClientUser, Message

    from integrations.base.interface import MessageParserProtocol
    from integrations.discord.config import SvcConfig


class SvcFunctions(FunctionsInterface):
    """discord専用関数"""

    def __init__(self, conf: "SvcConfig"):
        super().__init__()
        self.conf = conf
        """個別設定"""

    def post_processing(self, m: "MessageParserProtocol"):
        """後処理（非同期処理ラッパー）

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        asyncio.create_task(self.update_reaction(m))

    async def update_reaction(self, m: "MessageParserProtocol"):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        self.conf.bot_id = cast("ClientUser", self.conf.bot_id)
        self.conf.response = cast("Message", self.conf.response)

        EMOJI = {
            "ok": "\N{WHITE HEAVY CHECK MARK}",
            "ng": "\N{CROSS MARK}",
        }

        # 既に付いているリアクションを取得
        has_ok = False
        has_ng = False
        for reaction in self.conf.response.reactions:
            if str(reaction.emoji) == EMOJI["ok"]:
                async for user in reaction.users():
                    if user == self.conf.bot_id:
                        has_ok = True
                        continue
            if str(reaction.emoji) == EMOJI["ng"]:
                async for user in reaction.users():
                    if user == self.conf.bot_id:
                        has_ng = True
                        continue

        # リアクション処理
        match m.status.action:
            case "nothing":
                return
            case "change":
                if m.status.reaction:  # NGを外してOKを付ける
                    if has_ng:
                        await self.conf.response.remove_reaction(EMOJI["ng"], self.conf.bot_id)
                    if not has_ok:
                        await self.conf.response.add_reaction(EMOJI["ok"])
                else:  # OKを外してNGを付ける
                    if has_ok:
                        await self.conf.response.remove_reaction(EMOJI["ok"], self.conf.bot_id)
                    if not has_ng:
                        await self.conf.response.add_reaction(EMOJI["ng"])
            case "delete":
                if has_ok:
                    await self.conf.response.remove_reaction(EMOJI["ok"], self.conf.bot_id)
                if has_ng:
                    await self.conf.response.remove_reaction(EMOJI["ng"], self.conf.bot_id)

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        _ = m
        return {}
