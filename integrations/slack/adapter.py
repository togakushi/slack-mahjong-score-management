"""
integrations/slack/message.py
"""

import logging
from typing import cast

import pandas as pd
from slack_sdk.errors import SlackApiError

import libs.global_value as g
from integrations.base.interface import (APIInterface, LookupInterface,
                                         ReactionsInterface)
from integrations.protocols import MessageParserProtocol
from integrations.slack import api
from libs.utils import converter, formatter


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

        def _header_text(title: str) -> str:
            if not title.isnumeric() and title:  # 数値のキーはヘッダにしない
                return f"*【{title}】*\n"
            return ""

        def _table_data(data: dict) -> list:
            ret_list: list = []
            text_data = iter(data.values())
            # 先頭ブロックの処理
            v = next(text_data)
            if m.post.codeblock:
                ret_list.append(f"{header}```\n{v}\n```\n\n")
            else:
                ret_list.append(f"{header}{v}\n")
            # 残りのブロック
            for v in text_data:
                if m.post.codeblock:
                    ret_list.append(f"```\n{v}\n```\n\n")
                else:
                    ret_list.append(f"{v}\n")
            return ret_list

        if not m.in_thread:
            m.post.thread = False

        # 見出し
        if m.post.headline:
            title, text = next(iter(m.post.headline.items()))
            res = api.call_chat_post_message(
                channel=m.data.channel_id,
                text=f"{_header_text(title)}{text.rstrip()}",
                thread_ts=m.reply_ts,
            )
            if res.status_code == 200:  # 見出しがある場合はスレッドにする
                m.post.ts = res.get("ts", "undetermined")
            else:
                m.post.ts = "undetermined"

        # ファイルアップロード
        upload_flg: bool = False
        for attache_file in m.post.file_list:
            for title, file_path in attache_file.items():
                if file_path:
                    upload_flg = True
                    api.call_files_upload(
                        channel=m.data.channel_id,
                        title=title,
                        file=file_path,
                        thread_ts=m.reply_ts,
                        request_file_info=False,
                    )
        if upload_flg:
            return  # ファイルをポストしたら終了

        # 本文
        post_msg: list[str] = []
        for title, msg in m.post.message.items():
            header: str = str()
            if m.post.key_header:
                header = _header_text(title)

            if isinstance(msg, str):
                if m.post.codeblock:
                    post_msg.append(f"{header}```\n{msg.rstrip()}\n```\n\n")
                else:
                    post_msg.append(f"{header}{msg.rstrip()}\n")

            if isinstance(msg, pd.DataFrame):
                match m.data.command_type:
                    case "results":
                        match title:
                            case "通算ポイント" | "ポイント差分":
                                post_msg.extend(_table_data(converter.df_to_dict(msg, step=40)))
                            case "役満和了" | "卓外ポイント" | "その他":
                                if "回数" in msg.columns:
                                    post_msg.extend(_table_data(converter.df_to_count(msg, title, 1)))
                                else:
                                    post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                            case "座席データ":
                                post_msg.extend(_table_data(converter.df_to_seat_data(msg, 1)))
                            case "戦績":
                                if "name" in msg.columns:  # 縦持ちデータ
                                    pass
                                else:
                                    post_msg.extend(_table_data(converter.df_to_results_details(msg)))
                            case _:
                                post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                    case "rating":
                        post_msg.extend(_table_data(converter.df_to_dict(msg, step=20)))
                    case "ranking":
                        post_msg.extend(_table_data(converter.df_to_ranking(msg, title, step=50)))

        if m.post.summarize:
            post_msg = formatter.group_strings(post_msg)

        for msg in post_msg:
            api.call_chat_post_message(
                channel=m.data.channel_id,
                text=msg,
                thread_ts=m.reply_ts,
            )

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
