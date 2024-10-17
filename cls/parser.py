import logging

from slack_sdk import WebClient

import global_value as g


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
        self.text = str()
        self.thread_ts = str()
        _event = {}

        if "channel_name" in _body:
            if _body["channel_name"] == "directmessage":
                self.channel_id = _body["channel_id"]
                self.text = _body["text"]
                self.event_ts = "0"
        elif "container" in _body:
            self.channel_id = _body["user"]["id"]
        else:
            self.channel_id = _body["event"]["channel"]

            if "subtype" in _body["event"]:
                match _body["event"]["subtype"]:
                    case "message_changed":
                        self.status = "message_changed"
                        _event = _body["event"]["message"]
                    case "message_deleted":
                        self.status = "message_deleted"
                        _event = _body["event"]["previous_message"]
                    case "file_share":
                        self.status = "message_append"
                        _event = _body["event"]
                    case _:
                        logging.info(f"unknown subtype: {_body=}")
            else:
                self.status = "message_append"
                _event = _body["event"]

            for x in _event:
                match x:
                    case "user":
                        self.user_id = _event["user"]
                    case "ts":
                        self.event_ts = _event["ts"]
                    case "thread_ts":
                        self.thread_ts = _event["thread_ts"]
                    case "blocks":
                        try:
                            if "text" in _event["blocks"][0]["elements"][0]["elements"][0]:
                                self.text = _event["blocks"][0]["elements"][0]["elements"][0]["text"]
                            else:  # todo: 解析用出力
                                logging.info(f"<Not found: text> blocks in: {_event=}")
                        except Exception:
                            logging.error(f"<analysis> blocks in: {_event=}")

        if self.text:
            self.keyword = self.text.split()[0]
            self.argument = self.text.split()[1:]  # 最初のスペース以降はコマンド引数扱い

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

        self.check_updatable()

    def check_updatable(self):
        """
        DB更新可能チャンネルのポストかチェック
        """

        if not len(g.cfg.db.channel_limitations) or self.channel_id in g.cfg.db.channel_limitations.split(","):
            self.updatable = True
        else:
            self.updatable = False
