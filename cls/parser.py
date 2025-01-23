import logging

from slack_sdk import WebClient

import global_value as g
import lib.function.slack_api as slack_api


class Message_Parser():
    client: WebClient = WebClient()
    channel_id: str = str()
    user_id: str = str()
    text: str = str()  # post本文
    event_ts: str = str()  # テキストのまま処理する
    thread_ts: str = str()  # テキストのまま処理する
    status: str = str()  # event subtype
    keyword: str = str()
    argument: list = list()
    updatable: bool = bool()

    def __init__(self, body: dict = {}):
        if body is dict():
            self.parser(body)

    def parser(self, _body: dict):
        """
        postされたメッセージをパース
        """

        logging.trace(_body)

        __tmp_client = self.client
        self.__dict__.clear()
        self.client = __tmp_client
        self.text = _body.get("text")
        self.thread_ts = "0"
        _event = {}

        if _body.get("command") == g.cfg.setting.slash_command:
            if not self.channel_id:
                # スラッシュコマンド実行時のレスポンス先
                if _body.get("channel_name") == "directmessage":
                    self.channel_id = _body.get("channel_id")
                else:
                    self.channel_id = slack_api.get_dm_channel_id(_body.get("user_id"))

        if _body.get("event"):
            if not self.channel_id:
                # 呼び出しキーワードのレスポンス先
                if _body.get("channel_name") != "directmessage":
                    self.channel_id = _body["event"].get("channel")
                else:
                    self.channel_id = slack_api.get_dm_channel_id(_body.get("user_id"))

            match _body["event"].get("subtype"):
                case "message_changed":
                    self.status = "message_changed"
                    _event = _body["event"]["message"]
                case "message_deleted":
                    self.status = "message_deleted"
                    _event = _body["event"]["previous_message"]
                case "file_share":
                    self.status = "message_append"
                    _event = _body["event"]
                case None:
                    self.status = "message_append"
                    _event = _body["event"]
                case _:
                    self.status = "message_append"
                    _event = _body["event"]
                    logging.info(f"unknown subtype: {_body=}")

        self.user_id = _event.get("user")
        self.event_ts = _event.get("ts")
        self.thread_ts = _event.get("thread_ts", self.thread_ts)
        self.text = _event.get("text", self.text)

        if self.text:
            self.keyword = self.text.split()[0]
            self.argument = self.text.split()[1:]  # 最初のスペース以降はコマンド引数扱い
        else:  # text属性が見つからないときはログに出力
            logging.error(f"text not found: {_body=}")

        self.check_updatable()

    def parser_matches(self, _body: dict):
        """
        検索結果のログをパース
        """

        logging.trace(_body)

        __tmp_client = self.client
        self.__dict__.clear()
        self.client = __tmp_client
        self.channel_id = _body["channel"]["id"]
        self.user_id = _body["user"]
        self.text = _body["text"]
        self.event_ts = _body["ts"]
        self.thread_ts = None

        if "permalink" in _body:
            permalink = _body["permalink"]
            if permalink.split("?thread_ts=")[1:]:
                self.thread_ts = permalink.split("?thread_ts=")[1:][0]

        self.check_updatable()

    def check_updatable(self):
        """
        DB更新可能チャンネルのポストかチェック
        """

        if not len(g.cfg.db.channel_limitations) or self.channel_id in g.cfg.db.channel_limitations.split(","):
            self.updatable = True
        else:
            self.updatable = False
