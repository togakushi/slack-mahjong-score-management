"""
integrations/discord/functions.py
"""

import asyncio
from typing import TYPE_CHECKING, cast

from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from discord import ClientUser

    from integrations.base.interface import MessageParserProtocol
    from integrations.discord.config import SvcConfig
    from integrations.discord.api import AdapterAPI


class SvcFunctions(FunctionsInterface):
    """discord専用関数"""

    def __init__(self, api: "AdapterAPI", conf: "SvcConfig"):
        super().__init__()

        self.api = api
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

        EMOJI = {
            "ok": "\N{WHITE HEAVY CHECK MARK}",
            "ng": "\N{CROSS MARK}",
        }

        # 既に付いているリアクションを取得
        has_ok = False
        has_ng = False
        for reaction in self.api.response.reactions:
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
                        await self.api.response.remove_reaction(EMOJI["ng"], self.conf.bot_id)
                    if not has_ok:
                        await self.api.response.add_reaction(EMOJI["ok"])
                else:  # OKを外してNGを付ける
                    if has_ok:
                        await self.api.response.remove_reaction(EMOJI["ok"], self.conf.bot_id)
                    if not has_ng:
                        await self.api.response.add_reaction(EMOJI["ng"])
            case "delete":
                if has_ok:
                    await self.api.response.remove_reaction(EMOJI["ok"], self.conf.bot_id)
                if has_ng:
                    await self.api.response.remove_reaction(EMOJI["ng"], self.conf.bot_id)

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        _ = m
        return {}
