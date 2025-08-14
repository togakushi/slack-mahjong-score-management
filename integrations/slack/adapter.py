"""
integrations/slack/message.py
"""

import logging
from typing import cast

from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)
from integrations.protocols import MessageParserProtocol
from integrations.slack import api
from libs.utils import formatter


class _ReactionsAPI(ReactionsInterface):
    """リアクション操作"""
    def status(self, ch=str, ts=str) -> dict[str, list]:
        """botが付けたリアクションの種類を返す

        Args:
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ

        Returns:
            dict[str,list]: リアクション
        """

        icon: dict[str, list] = {
            "ok": [],
            "ng": [],
        }

        try:  # 削除済みメッセージはエラーになるので潰す
            res = g.appclient.reactions_get(channel=ch, timestamp=ts)
            logging.trace(res.validate())  # type: ignore
        except SlackApiError:
            return icon

        if (reactions := cast(dict, res["message"]).get("reactions")):
            for reaction in cast(list[dict], reactions):
                if g.cfg.setting.reaction_ok == reaction.get("name") and g.bot_id in reaction["users"]:
                    icon["ok"].append(res["message"]["ts"])
                if g.cfg.setting.reaction_ng == reaction.get("name") and g.bot_id in reaction["users"]:
                    icon["ng"].append(res["message"]["ts"])

        logging.info("ch=%s, ts=%s, user=%s, icon=%s", ch, ts, g.bot_id, icon)
        return icon

    def append(self, icon: str, ch: str, ts: str):
        api.call_reactions_add(icon=icon, ch=ch, ts=ts)

    def remove(self, icon: str, ch: str, ts: str):
        api.call_reactions_remove(icon=icon, ch=ch, ts=ts)


class _LookupAPI(LookupInterface):
    """情報取得"""
    def get_channel_id(self) -> str:
        """チャンネルIDを取得する

        Returns:
            str: チャンネルID
        """

        channel_id = ""

        try:
            response = g.webclient.search_messages(
                query=f"in:{g.cfg.search.channel}",
                count=1,
            )
            messages: dict = response.get("messages", {})
            if messages.get("matches"):
                channel = messages["matches"][0]["channel"]
                if isinstance(g.cfg.search.channel, str):
                    if channel["name"] in g.cfg.search.channel:
                        channel_id = channel["id"]
                else:
                    channel_id = channel["id"]
        except SlackApiError as e:
            logging.error(e)

        return channel_id

    def get_dm_channel_id(self, user_id: str) -> str:
        """DMのチャンネルIDを取得する

        Args:
            user_id (str): DMの相手

        Returns:
            str: チャンネルID
        """

        channel_id = ""

        try:
            response = g.appclient.conversations_open(users=[user_id])
            channel_id = response["channel"]["id"]
        except SlackApiError as e:
            logging.error(e)

        return channel_id


class SlackAPI(APIInterface):
    """Slack API操作クラス"""

    def __init__(self):
        self.lookup = _LookupAPI()
        self.reactions = _ReactionsAPI()

    def post(self, m: MessageParserProtocol):
        """メッセージをポストする

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        if not m.in_thread:
            m.post.thread = False

        # 見出し
        if m.post.headline:
            res = api.call_chat_post_message(
                channel=m.data.channel_id,
                text=m.post.headline.rstrip(),
                thread_ts=m.reply_ts,
            )
            if res:
                m.post.ts = res.get("ts", "undetermined")
                m.post.thread = True  # 見出しがある場合はスレッドにする
            else:
                m.post.ts = "undetermined"

        # 本文
        if m.post.file_list:
            if self.fileupload(m):
                return  # ファイルをポストしたら終了

        post_msg: list = []
        for k, v in m.post.message.items():
            text = ""
            if k.isnumeric():  # 数値のキーにはヘッダは付けない
                if m.post.codeblock:
                    post_msg.append(f"```\n{v}\n```\n")
                else:
                    post_msg.append(f"{v}\n")
            else:
                if m.post.key_header:
                    text += f"*【{k}】*\n{text.rstrip()}\n"
                text += f"```\n{v.rstrip()}\n```\n" if m.post.codeblock else v
            post_msg.append(text + "\n")

        if m.post.summarize:
            post_msg = formatter.group_strings(post_msg)

        for msg in post_msg:
            api.call_chat_post_message(
                channel=m.data.channel_id,
                text=msg,
                thread_ts=m.reply_ts,
            )

    def fileupload(self, m: MessageParserProtocol) -> dict:
        """files_upload_v2に渡すパラメータを設定

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """

        res: SlackResponse | None = None
        for attache_file in m.post.file_list:
            for title, file_path in attache_file.items():
                if title == "dummy":
                    continue
                if file_path:
                    res = api.call_files_upload(
                        channel=m.data.channel_id,
                        title=title,
                        file=file_path,
                        thread_ts=m.reply_ts,
                        request_file_info=False,
                    )

        if isinstance(res, SlackResponse):
            return cast(dict, res)
        return {}

    def get_conversations(self, m: MessageParserProtocol) -> dict:
        """スレッド情報の取得

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """

        try:
            res = g.appclient.conversations_replies(channel=m.data.channel_id, ts=m.data.event_ts)
            logging.trace(res.validate())  # type: ignore
            return cast(dict, res)
        except SlackApiError as e:
            logging.error(e)
            return {}
