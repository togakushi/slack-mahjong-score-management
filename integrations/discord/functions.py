"""
integrations/discord/functions.py
"""

from typing import TYPE_CHECKING, cast

from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from discord import ClientUser, Message

    from integrations.base.interface import MessageParserProtocol
    from integrations.discord.api import AdapterAPI
    from integrations.discord.config import SvcConfig


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

        match m.status.action:
            case "nothing":
                return
            case "change":
                self.api.bot.loop.create_task(self.update_reaction(m))
            case "delete":
                self.api.bot.loop.create_task(self.delete_reaction())

    async def update_reaction(self, m: "MessageParserProtocol"):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        if await self.is_deleted_message(self.api.response):
            return

        self.conf.bot_name = cast("ClientUser", self.conf.bot_name)

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
                    if user == self.api.response.guild.me:
                        has_ok = True
                        continue
            if str(reaction.emoji) == EMOJI["ng"]:
                async for user in reaction.users():
                    if user == self.api.response.guild.me:
                        has_ng = True
                        continue

        # リアクション処理
        if m.status.reaction:  # NGを外してOKを付ける
            if has_ng:
                await self.api.response.remove_reaction(EMOJI["ng"], self.conf.bot_name)
            if not has_ok:
                await self.api.response.add_reaction(EMOJI["ok"])
        else:  # OKを外してNGを付ける
            if has_ok:
                await self.api.response.remove_reaction(EMOJI["ok"], self.conf.bot_name)
            if not has_ng:
                await self.api.response.add_reaction(EMOJI["ng"])

    async def delete_reaction(self):
        """botが付けたリアクションをすべて削除する"""

        if await self.is_deleted_message(self.api.response):
            return

        for reaction in self.api.response.reactions:
            async for user in reaction.users():
                if user == self.api.response.guild.me:
                    await reaction.remove(user)

    async def is_deleted_message(self, message: "Message") -> bool:
        """メッセージが削除済みか調べる

        Args:
            message (Message): discordオブジェクト

        Returns:
            bool: 真偽
        """
        try:
            await message.channel.fetch_message(message.id)
            return False
        except Exception:
            return True

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        _ = m
        return {}
