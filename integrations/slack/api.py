"""
integrations/slack/api.py
"""

import logging
from typing import Any, cast

import pandas as pd
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.base.interface import APIInterface
from integrations.protocols import MessageParserProtocol
from integrations.slack.adapter import AdapterInterface
from libs.utils import converter, formatter


class SlackAPI(APIInterface):
    """Slack API操作クラス"""

    def __init__(self, adapter: AdapterInterface):
        super().__init__()
        self.adapter = adapter

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
                ret_list.append(f"{header}```\n{v}\n```\n")
            else:
                ret_list.append(f"{header}{v}\n")
            # 残りのブロック
            for v in text_data:
                if m.post.codeblock:
                    ret_list.append(f"```\n{v}\n```\n")
                else:
                    ret_list.append(f"{v}\n")
            return ret_list

        if not m.in_thread:
            m.post.thread = False

        # 見出し
        if m.post.headline:
            title, text = next(iter(m.post.headline.items()))
            res = call_chat_post_message(
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
                    call_files_upload(
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
                    post_msg.append(f"{header}```\n{msg.rstrip()}\n```\n")
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
                                if "東家 名前" in msg.columns:  # 縦持ちデータ
                                    post_msg.extend(_table_data(converter.df_to_results_details(msg)))
                                else:
                                    post_msg.extend(_table_data(converter.df_to_results_simple(msg)))
                            case _:
                                post_msg.extend(_table_data(converter.df_to_remarks(msg)))
                    case "rating":
                        post_msg.extend(_table_data(converter.df_to_dict(msg, step=20)))
                    case "ranking":
                        post_msg.extend(_table_data(converter.df_to_ranking(msg, title, step=50)))

        if m.post.summarize:
            post_msg = formatter.group_strings(post_msg)

        for msg in post_msg:
            call_chat_post_message(
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
            res = self.adapter.conf.appclient.conversations_replies(channel=m.data.channel_id, ts=m.data.event_ts)
            logging.trace(res.validate())  # type: ignore
            return cast(dict, res)
        except SlackApiError as e:
            logging.error(e)
            return {}

    def reaction_status(self, ch=str, ts=str) -> dict[str, list]:
        """botが付けたリアクションの種類を返す

        Args:
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ

        Returns:
            dict[str,list]: リアクション
        """

        ok = getattr(self.adapter.conf, "reaction_ok", "ok")
        ng = getattr(self.adapter.conf, "reaction_ng", "ng")

        icon: dict[str, list] = {
            "ok": [],
            "ng": [],
        }

        try:  # 削除済みメッセージはエラーになるので潰す
            res = self.adapter.conf.appclient.reactions_get(channel=ch, timestamp=ts)
            logging.trace(res.validate())  # type: ignore
        except SlackApiError:
            return icon

        if (reactions := cast(dict, res["message"]).get("reactions")):
            for reaction in cast(list[dict], reactions):
                if ok == reaction.get("name") and self.adapter.conf.bot_id in reaction["users"]:
                    icon["ok"].append(res["message"]["ts"])
                if ng == reaction.get("name") and self.adapter.conf.bot_id in reaction["users"]:
                    icon["ng"].append(res["message"]["ts"])

        logging.info("ch=%s, ts=%s, user=%s, icon=%s", ch, ts, self.adapter.conf.bot_id, icon)
        return icon

    def reaction_append(self, icon: str, ch: str, ts: str):
        """リアクション追加

        Args:
            icon (str): リアクション文字
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ
        """

        call_reactions_add(icon=icon, ch=ch, ts=ts)

    def reaction_remove(self, icon: str, ch: str, ts: str):
        """リアクション削除

        Args:
            icon (str): リアクション文字
            ch (str): チャンネルID
            ts (str): メッセージのタイムスタンプ
        """

        call_reactions_remove(icon=icon, ch=ch, ts=ts)


def call_chat_post_message(**kwargs) -> SlackResponse:
    """slackにメッセージをポストする

    Returns:
        SlackResponse: API response
    """

    g.adapter = cast(AdapterInterface, g.adapter)

    res = cast(SlackResponse, {})
    if kwargs["thread_ts"] == "0":
        kwargs.pop("thread_ts")

    try:
        res = g.adapter.conf.appclient.chat_postMessage(**kwargs)
    except SlackApiError as err:
        logging.critical(err)
        logging.error("kwargs=%s", kwargs)

    return res


def call_files_upload(**kwargs) -> SlackResponse | Any:
    """slackにファイルをアップロードする

    Returns:
        SlackResponse | Any: API response
    """

    g.adapter = cast(AdapterInterface, g.adapter)

    res = None
    if kwargs.get("thread_ts", "0") == "0":
        kwargs.pop("thread_ts")

    try:
        res = g.adapter.conf.appclient.files_upload_v2(**kwargs)
    except SlackApiError as err:
        logging.critical(err)
        logging.error("kwargs=%s", kwargs)

    return res


def call_reactions_add(icon: str, ch: str, ts: str):
    """リアクションを付ける

    Args:
        icon (str): 付けるリアクション
        ch (str): チャンネルID
        ts (str): メッセージのタイムスタンプ
    """

    g.adapter = cast(AdapterInterface, g.adapter)

    if not all([icon, ch, ts]):
        logging.warning("deficiency: ts=%s, ch=%s, icon=%s", ts, ch, icon)
        return

    try:
        res: SlackResponse = g.adapter.conf.appclient.reactions_add(
            channel=str(ch),
            name=icon,
            timestamp=str(ts),
        )
        logging.info("ts=%s, ch=%s, icon=%s, %s", ts, ch, icon, res.validate())
    except SlackApiError as err:
        match cast(dict, err.response).get("error"):
            case "already_reacted":
                pass
            case _:
                logging.critical(err)
                logging.critical("ts=%s, ch=%s, icon=%s", ts, ch, icon)


def call_reactions_remove(icon: str, ch: str, ts: str):
    """リアクションを外す

    Args:
        icon (str): 外すリアクション
        ch (str): チャンネルID
        ts (str): メッセージのタイムスタンプ
    """

    g.adapter = cast(AdapterInterface, g.adapter)

    if not all([icon, ch, ts]):
        logging.warning("deficiency: ts=%s, ch=%s, icon=%s", ts, ch, icon)
        return

    try:
        res = g.adapter.conf.appclient.reactions_remove(
            channel=ch,
            name=icon,
            timestamp=ts,
        )
        logging.info("ch=%s, ts=%s, icon=%s, %s", ch, ts, icon, res.validate())
    except SlackApiError as err:
        match cast(dict, err.response).get("error"):
            case "no_reaction":
                pass
            case "message_not_found":
                pass
            case _:
                logging.critical(err)
                logging.critical("ch=%s, ts=%s, icon=%s", ch, ts, icon)
