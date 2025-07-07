"""
integrations/slack/message.py
"""

import logging
from typing import cast

from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.base.message import MessageInterface
from integrations.slack import api


class SlackMessage(MessageInterface):
    def post_message(self, msg: str, ts=False) -> SlackResponse:
        """メッセージをポストする

        Args:
            message (str): ポストするメッセージ
            ts (bool, optional): スレッドに返す. Defaults to False.

        Returns:
            SlackResponse: API response
        """

        if not ts and g.msg.thread_ts:
            ts = g.msg.thread_ts

        res = api.post.call_chat_post_message(
            channel=g.msg.channel_id,
            text=f"{msg.strip()}",
            thread_ts=ts,
        )

        return res

    def post_multi_message(self, msg: dict, ts: bool | None = False, summarize: bool = True) -> None:
        """メッセージを分割してポスト

        Args:
            msg (dict): ポストするメッセージ
            ts (bool, optional): スレッドに返す. Defaults to False.
            summarize (bool, optional): 可能な限り1つのブロックにまとめる. Defaults to True.
        """

        if isinstance(msg, dict):
            if summarize:  # まとめてポスト
                key_list = list(map(str, msg.keys()))
                post_msg = msg[key_list[0]]
                for i in key_list[1:]:
                    if len((post_msg + msg[i])) < 3800:  # 3800文字を超える直前までまとめる
                        post_msg += msg[i]
                    else:
                        self.post_message(post_msg, ts)
                        post_msg = msg[i]
                self.post_message(post_msg, ts)
            else:  # そのままポスト
                for i in msg.keys():
                    self.post_message(msg[i], ts)
        else:
            self.post_message(msg, ts)

    def post(self, **kwargs):
        """パラメータの内容によって呼び出すAPIを振り分ける"""

        logging.debug(kwargs)
        headline = str(kwargs.get("headline", ""))
        msg = kwargs.get("message")
        summarize = bool(kwargs.get("summarize", True))
        file_list = cast(dict, kwargs.get("file_list", {"dummy": ""}))

        # 見出しポスト
        if (res := self.post_message(headline)):
            ts = res.get("ts", False)
        else:
            ts = False

        # 本文ポスト
        for x in file_list:
            if (file_path := file_list.get(x)):
                self.fileupload(str(x), str(file_path), ts)
                msg = {}  # ファイルがあるメッセージは不要

        if msg:
            self.post_multi_message(msg, ts, summarize)

    def fileupload(self, title: str, file: str | bool, ts: str | bool = False) -> SlackResponse | None:
        """files_upload_v2に渡すパラメータを設定

        Args:
            title (str): タイトル行
            file (str): アップロードファイルパス
            ts (str | bool, optional): スレッドに返す. Defaults to False.

        Returns:
            SlackResponse | None: 結果
        """

        if not ts and g.msg.thread_ts:
            ts = g.msg.thread_ts

        res = api.post.call_files_upload(
            channel=g.msg.channel_id,
            title=title,
            file=file,
            thread_ts=ts,
            request_file_info=False,
        )

        return res
