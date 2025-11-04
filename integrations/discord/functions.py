"""
integrations/discord/functions.py
"""

from typing import TYPE_CHECKING, cast

from discord import Forbidden, NotFound
from discord.channel import TextChannel

from cls.timekit import ExtendedDatetime as ExtDt
from integrations.base.interface import FunctionsInterface

if TYPE_CHECKING:
    from discord import ClientUser, Message

    from integrations.base.interface import MessageParserProtocol
    from integrations.discord.api import AdapterAPI
    from integrations.discord.config import SvcConfig
    from integrations.discord.parser import MessageParser


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
                self.api.bot.loop.create_task(self.delete_reaction(m))

    async def update_reaction(self, m: "MessageParserProtocol"):
        """後処理

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        m = cast("MessageParser", m)
        self.conf.bot_name = cast("ClientUser", self.conf.bot_name)

        if not getattr(m, "discord_msg"):
            return
        if await self.is_deleted_message(m.discord_msg):
            return

        EMOJI = {
            "ok": "\N{WHITE HEAVY CHECK MARK}",
            "ng": "\N{CROSS MARK}",
        }

        # 既に付いているリアクションを取得
        has_ok = False
        has_ng = False
        for reaction in m.discord_msg.reactions:
            if str(reaction.emoji) == EMOJI["ok"]:
                async for user in reaction.users():
                    if user == self.conf.bot_name:
                        has_ok = True
                        continue
            if str(reaction.emoji) == EMOJI["ng"]:
                async for user in reaction.users():
                    if user == self.conf.bot_name:
                        has_ng = True
                        continue

        # リアクション処理
        if m.status.reaction:  # NGを外してOKを付ける
            if has_ng:
                await m.discord_msg.remove_reaction(EMOJI["ng"], self.conf.bot_name)
            if not has_ok:
                await m.discord_msg.add_reaction(EMOJI["ok"])
        else:  # OKを外してNGを付ける
            if has_ok:
                await m.discord_msg.remove_reaction(EMOJI["ok"], self.conf.bot_name)
            if not has_ng:
                await m.discord_msg.add_reaction(EMOJI["ng"])

    async def delete_reaction(self, m: "MessageParserProtocol"):
        """botが付けたリアクションをすべて削除する

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        m = cast("MessageParser", m)

        if hasattr(m, "discord_msg"):
            if await self.is_deleted_message(m.discord_msg):
                return  # 削除済み
        else:  # Messageを持っていない場合はevent_tsとchannel_idを使って検索を試みる
            if not m.data.channel_id:
                return  # チャンネルIDが空
            channel = self.api.bot.get_channel(int(m.data.channel_id))
            if not isinstance(channel, TextChannel):
                return  # 対象外チャンネル

            async for msg in channel.history(
                limit=10,
                oldest_first=True,
                after=ExtDt(float(m.data.event_ts), seconds=-1).dt,
                before=ExtDt(float(m.data.event_ts), seconds=1).dt,
            ):
                if str(msg.created_at.timestamp()) == m.data.event_ts:
                    m.discord_msg = cast("Message", msg)
                    break
                return  # 該当メッセージなし(削除済み)

        for reaction in m.discord_msg.reactions:
            async for user in reaction.users():
                if user == self.conf.bot_name:
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
        except NotFound:
            return True
        except Forbidden:
            return True

    def get_conversations(self, m: "MessageParserProtocol") -> dict:
        _ = m
        return {}
