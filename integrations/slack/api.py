"""
integrations/slack/api.py
"""

import logging
import textwrap
from pathlib import PosixPath
from typing import TYPE_CHECKING, cast

import pandas as pd

from integrations.base.interface import APIInterface
from integrations.protocols import CommandType
from libs.utils import converter, formatter

if TYPE_CHECKING:
    from slack_sdk.web import SlackResponse
    from slack_sdk.web.client import WebClient

    from integrations.protocols import MessageParserProtocol


class AdapterAPI(APIInterface):
    """インターフェースAPI操作クラス"""

    # slack object
    appclient: "WebClient"
    """WebClient(botトークン使用)"""
    webclient: "WebClient"
    """WebClient(userトークン使用)"""

    def __init__(self):
        super().__init__()

        try:
            from slack_sdk.errors import SlackApiError

            self.slack_api_error = SlackApiError
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(err.msg) from None

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
            # 先頭ブロックの処理(ヘッダ追加)
            v = next(text_data)
            ret_list.append(f"{header}```\n{v}\n```\n" if options.codeblock else f"{header}{v}\n")
            # 残りのブロック
            for v in text_data:
                ret_list.append(f"```\n{v}\n```\n" if options.codeblock else f"```\n{v}\n```\n")
            return ret_list

        def _post_header():
            res = self._call_chat_post_message(
                channel=m.data.channel_id,
                text=f"{_header_text(header_title)}{header_text.rstrip()}",
                thread_ts=m.reply_ts,
            )
            if res.status_code == 200:  # 見出しがある場合はスレッドにする
                m.post.ts = res.get("ts", "undetermined")
            else:
                m.post.ts = "undetermined"

        if not m.in_thread:
            m.post.thread = False

        # 見出しポスト
        header_title = ""
        header_text = ""
        if m.post.headline:
            header_title, header_text = next(iter(m.post.headline.items()))
            if not m.post.message:  # メッセージなし
                _post_header()
            elif not all(options.header_hidden for _, options in m.post.message):
                _post_header()

        # 本文
        post_msg: list[str] = []
        for data, options in m.post.message:
            header = ""

            if isinstance(data, PosixPath) and data.exists():
                comment = textwrap.dedent(f"{_header_text(header_title)}{header_text.rstrip()}") if options.use_comment else ""
                self._call_files_upload(
                    channel=m.data.channel_id,
                    title=options.title,
                    file=str(data),
                    initial_comment=comment,
                    thread_ts=m.reply_ts,
                    request_file_info=False,
                )

            if isinstance(data, str):
                if options.key_title and (options.title != header_title):
                    header = _header_text(options.title)
                post_msg.append(f"{header}```\n{data.rstrip()}\n```\n" if options.codeblock else f"{header}{data.rstrip()}\n")

            if isinstance(data, pd.DataFrame):
                if options.key_title and (options.title != header_title):
                    header = _header_text(options.title)

                match m.status.command_type:
                    case CommandType.RESULTS:
                        match options.title:
                            case "通算ポイント" | "ポイント差分":
                                post_msg.extend(_table_data(converter.df_to_text_table(data, step=40)))
                            case "役満和了" | "卓外清算" | "その他":
                                if "回数" in data.columns:
                                    post_msg.extend(_table_data(converter.df_to_count(data, options.title, 1)))
                                else:
                                    post_msg.extend(_table_data(converter.df_to_remarks(data)))
                            case "成績詳細比較":
                                post_msg.extend(_table_data(converter.df_to_text_table2(data, options, 3800)))
                            case "座席データ":
                                post_msg.extend(_table_data(converter.df_to_seat_data(data, 1)))
                            case "戦績":
                                if "東家 名前" in data.columns:  # 縦持ちデータ
                                    post_msg.extend(_table_data(converter.df_to_results_details(data)))
                                else:
                                    post_msg.extend(_table_data(converter.df_to_results_simple(data)))
                            case _:
                                post_msg.extend(_table_data(converter.df_to_remarks(data)))
                    case CommandType.RATING:
                        post_msg.extend(_table_data(converter.df_to_text_table(data, step=20)))
                    case CommandType.RANKING:
                        post_msg.extend(_table_data(converter.df_to_ranking(data, options.title, step=50)))
                    case _:
                        pass

        if options.summarize:
            post_msg = formatter.group_strings(post_msg)

        for msg in post_msg:
            self._call_chat_post_message(
                channel=m.data.channel_id,
                text=msg,
                thread_ts=m.reply_ts,
            )

    def _call_chat_post_message(self, **kwargs) -> "SlackResponse":
        """slackにメッセージをポストする

        Returns:
            SlackResponse: API response
        """

        res = cast("SlackResponse", {})
        if kwargs["thread_ts"] == "0":
            kwargs.pop("thread_ts")

        try:
            res = self.appclient.chat_postMessage(**kwargs)
        except self.slack_api_error as err:
            logging.error("slack_api_error: %s", err)
            logging.error("kwargs=%s", kwargs)

        return res

    def _call_files_upload(self, **kwargs) -> "SlackResponse":
        """slackにファイルをアップロードする

        Returns:
            SlackResponse | Any: API response
        """

        res = cast("SlackResponse", {})
        if kwargs.get("thread_ts", "0") == "0":
            kwargs.pop("thread_ts")

        try:
            res = self.appclient.files_upload_v2(**kwargs)
        except self.slack_api_error as err:
            logging.error("slack_api_error: %s", err)
            logging.error("kwargs=%s", kwargs)

        return res
