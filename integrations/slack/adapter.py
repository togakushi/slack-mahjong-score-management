"""
integrations/slack/message.py
"""

import copy
import logging
import re
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

    def post_message(self, m: MessageParserProtocol) -> dict:
        """メッセージをポストする
        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """

        if isinstance(m.post.message, dict):
            k, v = next(iter(m.post.message.items()))  # 先頭のみ処理
            text = f"```\n{v.rstrip()}\n```" if m.post.codeblock else v
            if isinstance(k, str) and k and m.post.key_header:
                text = f"*【{k}】*\n{text}"
        else:
            text = m.post.message

        res = api.call_chat_post_message(
            channel=m.data.channel_id,
            text=text,
            thread_ts=m.reply_ts,
        )

        return cast(dict, res)

    def post_multi_message(self, m: MessageParserProtocol) -> None:
        """メッセージを分割してポスト

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        tmp_m = copy.deepcopy(m)
        if isinstance(m.post.message, dict):
            # テキストブロック生成
            text_block: list = []
            for k, v in m.post.message.items():
                text = f"```\n{v.rstrip()}\n```" if m.post.codeblock else v
                if isinstance(k, str) and k and m.post.key_header:
                    text_block.append(f"*【{k}】*\n{text.rstrip()}\n")
                else:
                    text_block.append(f"{text.rstrip()}\n")

            if m.post.summarize:
                for text in formatter.group_strings(text_block):
                    tmp_m.post.message = text
                    self.post_message(tmp_m)
            else:
                for text in text_block:
                    tmp_m.post.message = text
                    self.post_message(tmp_m)
        else:
            self.post_message(m)

    def post_text(self, m: MessageParserProtocol) -> dict:
        """コードブロック修飾付きポスト

        Args:
            m (MessageParserProtocol): メッセージデータ

        Returns:
            dict: API response
        """

        if isinstance(m.post.message, dict):  # 辞書型のメッセージは受け付けない
            return {}

        # コードブロック修飾付きポスト
        if len(re.sub(r"\n+", "\n", f"{m.post.message.strip()}").splitlines()) == 1:
            res = api.call_chat_post_message(
                channel=m.data.channel_id,
                text=f"{m.post.title}\n{m.post.message.strip()}",
                thread_ts=m.reply_ts,
            )
        else:
            # ポスト予定のメッセージをstep行単位のブロックに分割
            step = 50
            post_msg: list[str] = []
            for count in range(int(len(m.post.message.splitlines()) / step) + 1):
                post_msg.append(
                    "\n".join(m.post.message.splitlines()[count * step:(count + 1) * step])
                )

            # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
            if len(post_msg) > 1 and step / 2 > len(post_msg[count].splitlines()):
                post_msg[count - 1] += "\n" + post_msg.pop(count)

            # ブロック単位でポスト
            for _, val in enumerate(post_msg):
                res = api.call_chat_post_message(
                    channel=m.data.channel_id,
                    text=f"\n{m.post.title}\n\n```{val.rstrip()}```",
                    thread_ts=m.reply_ts,
                )

        return cast(dict, res)

    def post(self, m: MessageParserProtocol):
        """パラメータの内容によって呼び出すAPIを振り分ける

        Args:
            m (MessageParserProtocol): メッセージデータ
        """

        if m.post.headline:  # 見出し付き
            tmp_m = copy.deepcopy(m)
            tmp_m.post.message = m.post.headline
            if (res := self.post_message(tmp_m)):
                m.post.ts = res.get("ts", "undetermined")
                m.post.thread = True  # 見出しがある場合はスレッドにする
            else:
                m.post.ts = "undetermined"

        # 本文ポスト
        if m.post.file_list:
            if self.fileupload(m):
                return  # ファイルをポストしたら終了

        if isinstance(m.post.message, dict):
            self.post_multi_message(m)
        elif m.post.message:
            self.post_message(m)

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
