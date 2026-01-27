"""
integrations/slack/api.py
"""

import logging
import textwrap
from pathlib import PosixPath
from typing import TYPE_CHECKING, cast

import pandas as pd

from integrations.base.interface import APIInterface
from libs.types import StyleOptions
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
                ret_list.append(f"```\n{v}\n```\n" if options.codeblock else f"{v}\n")

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
        options = StyleOptions()
        post_msg: list[str] = []
        block_layout = False
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
                text_body = textwrap.indent(data.rstrip(), "\t" * options.indent)
                post_msg.append(f"{header}```\n{text_body}\n```\n" if options.codeblock else f"{header}{text_body}\n")

            if isinstance(data, pd.DataFrame):
                if options.key_title and (options.title != header_title):
                    header = _header_text(options.title)
                match options.data_kind:
                    case StyleOptions.DataKind.POINTS_TOTAL | StyleOptions.DataKind.POINTS_DIFF:
                        post_msg.extend(_table_data(converter.df_to_text_table(data, options, step=40)))
                    case StyleOptions.DataKind.REMARKS_YAKUMAN | StyleOptions.DataKind.REMARKS_REGULATION | StyleOptions.DataKind.REMARKS_OTHER:
                        options.indent = 1
                        post_msg.extend(_table_data(converter.df_to_remarks(data, options)))
                    case StyleOptions.DataKind.DETAILED_COMPARISON:
                        post_msg.extend(_table_data(converter.df_to_text_table2(data, options, limit=3800)))
                    case StyleOptions.DataKind.SEAT_DATA:
                        options.indent = 1
                        post_msg.extend(_table_data(converter.df_to_seat_data(data, options)))
                    case StyleOptions.DataKind.RECORD_DATA:
                        block_layout = True
                        post_msg.extend(_table_data(converter.df_to_results_simple(data, options, limit=1900)))
                    case StyleOptions.DataKind.RECORD_DATA_ALL:
                        post_msg.extend(_table_data(converter.df_to_results_details(data, options, limit=2600)))
                    case StyleOptions.DataKind.RANKING:
                        post_msg.extend(_table_data(converter.df_to_ranking(data, options.title, step=50)))
                    case StyleOptions.DataKind.RATING:
                        post_msg.extend(_table_data(converter.df_to_text_table(data, options, step=20)))
                    case _:
                        pass

        if options.summarize:
            post_msg = formatter.group_strings(post_msg)

        for msg in post_msg:
            if msg != msg.lstrip() or (not msg.find("*【戦績】*") and block_layout):
                self._call_chat_post_message(
                    channel=m.data.channel_id,
                    text=msg.rstrip(),
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": msg.rstrip()}}],
                    thread_ts=m.reply_ts,
                )
            else:
                self._call_chat_post_message(
                    channel=m.data.channel_id,
                    text=msg.rstrip(),
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
