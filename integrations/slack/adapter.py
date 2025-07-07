"""
integrations/slack/message.py
"""

import logging
import re
from typing import cast

from slack_sdk.web import SlackResponse

import libs.global_value as g
from integrations.base.adapter import APIInterface
from integrations.slack import api


class SlackAPI(APIInterface):
    def post_message(self, msg: str, ts=False) -> dict:
        """メッセージをポストする

        Args:
            message (str): ポストするメッセージ
            ts (bool, optional): スレッドに返す. Defaults to False.

        Returns:
            dict: API response
        """

        if not ts and g.msg.thread_ts:
            ts = g.msg.thread_ts

        res = api.call_chat_post_message(
            channel=g.msg.channel_id,
            text=f"{msg.strip()}",
            thread_ts=ts,
        )

        return cast(dict, res)

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

    def post_text(self, event_ts: str, title: str, msg: str) -> dict:
        """コードブロック修飾付きポスト

        Args:
            event_ts (str): スレッドに返す
            title (str): タイトル行
            msg (str): 本文

        Returns:
            dict | Any: API response
        """

        # コードブロック修飾付きポスト
        if len(re.sub(r"\n+", "\n", f"{msg.strip()}").splitlines()) == 1:
            res = api.call_chat_post_message(
                channel=g.msg.channel_id,
                text=f"{title}\n{msg.strip()}",
                thread_ts=event_ts,
            )
        else:
            # ポスト予定のメッセージをstep行単位のブロックに分割
            step = 50
            post_msg = []
            for count in range(int(len(msg.splitlines()) / step) + 1):
                post_msg.append(
                    "\n".join(msg.splitlines()[count * step:(count + 1) * step])
                )

            # 最終ブロックがstepの半分以下なら直前のブロックにまとめる
            if len(post_msg) > 1 and step / 2 > len(post_msg[count].splitlines()):
                post_msg[count - 1] += "\n" + post_msg.pop(count)

            # ブロック単位でポスト
            for _, val in enumerate(post_msg):
                res = api.call_chat_post_message(
                    channel=g.msg.channel_id,
                    text=f"\n{title}\n\n```{val.strip()}```",
                    thread_ts=event_ts,
                )

        return cast(dict, res)

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

        res = api.call_files_upload(
            channel=g.msg.channel_id,
            title=title,
            file=file,
            thread_ts=ts,
            request_file_info=False,
        )

        return res
