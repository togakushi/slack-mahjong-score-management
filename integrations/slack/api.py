"""
integrations/slack/api.py
"""

import logging
import textwrap
from typing import TYPE_CHECKING, Any, cast

import pandas as pd
from slack_sdk.errors import SlackApiError
from slack_sdk.web import SlackResponse

from integrations.base.interface import APIInterface
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from integrations.protocols import MessageParserProtocol
    from integrations.slack.config import SvcConfig


class AdapterAPI(APIInterface):
    """インターフェースAPI操作クラス"""

    def __init__(self, conf: "SvcConfig"):
        super().__init__()
        self.conf = conf

    def post(self, m: "MessageParserProtocol"):
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

        # 見出し取得
        text = ""
        title = ""
        if m.post.headline:
            title, text = next(iter(m.post.headline.items()))

        # ファイルアップロード
        upload_flg: bool = False
        for attache_file in m.post.file_list:
            for title, file_path in attache_file.items():
                if file_path:
                    upload_flg = True
                    self._call_files_upload(
                        channel=m.data.channel_id,
                        title=title,
                        file=file_path,
                        initial_comment=textwrap.dedent(text),
                        thread_ts=m.reply_ts,
                        request_file_info=False,
                    )
        if upload_flg:
            return  # ファイルをポストしたら終了

        # 見出しポスト
        if m.post.headline:
            res = self._call_chat_post_message(
                channel=m.data.channel_id,
                text=f"{_header_text(title)}{text.rstrip()}",
                thread_ts=m.reply_ts,
            )
            if res.status_code == 200:  # 見出しがある場合はスレッドにする
                m.post.ts = res.get("ts", "undetermined")
            else:
                m.post.ts = "undetermined"

        # 本文ポスト
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
            self._call_chat_post_message(
                channel=m.data.channel_id,
                text=msg,
                thread_ts=m.reply_ts,
            )

    def _call_chat_post_message(self, **kwargs) -> SlackResponse:
        """slackにメッセージをポストする

        Returns:
            SlackResponse: API response
        """

        res = cast(SlackResponse, {})
        if kwargs["thread_ts"] == "0":
            kwargs.pop("thread_ts")

        try:
            res = self.conf.appclient.chat_postMessage(**kwargs)
        except SlackApiError as err:
            logging.critical(err)
            logging.error("kwargs=%s", kwargs)

        return res

    def _call_files_upload(self, **kwargs) -> SlackResponse | Any:
        """slackにファイルをアップロードする

        Returns:
            SlackResponse | Any: API response
        """

        res = None
        if kwargs.get("thread_ts", "0") == "0":
            kwargs.pop("thread_ts")

        try:
            res = self.conf.appclient.files_upload_v2(**kwargs)
        except SlackApiError as err:
            logging.critical(err)
            logging.error("kwargs=%s", kwargs)

        return res
