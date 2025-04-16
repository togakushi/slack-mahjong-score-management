"""
cls/parser.py
"""

import logging

from slack_sdk import WebClient

import libs.global_value as g
from libs.data import lookup


class MessageParser():
    """メッセージ解析クラス"""
    client: WebClient = WebClient()
    channel_id: str | None = str()
    channel_type: str | None = str()
    user_id: str = str()
    text: str | None = str()  # post本文
    event_ts: str = str()  # テキストのまま処理する
    thread_ts: str = str()  # テキストのまま処理する
    status: str = str()  # event subtype
    keyword: str = str()
    argument: list = []
    updatable: bool = bool()
    in_thread: bool = bool()

    def __init__(self, body: dict | None = None):
        if isinstance(body, dict):
            self.parser(body)

    def parser(self, _body: dict):
        """postされたメッセージをパースする

        Args:
            _body (dict): postされたデータ
        """

        logging.trace(_body)  # type: ignore

        __tmp_client = self.client
        self.__dict__.clear()
        self.client = __tmp_client
        self.text = ""
        self.thread_ts = "0"
        self.keyword = ""
        self.argument = []

        if _body.get("command") == g.cfg.setting.slash_command:  # スラッシュコマンド
            _event = _body
            if not self.channel_id:
                if _body.get("channel_name") == "directmessage":
                    self.channel_id = _body.get("channel_id", None)
                else:
                    self.channel_id = lookup.api.get_dm_channel_id(_body.get("user_id", ""))

        if _body.get("container"):  # Homeタブ
            self.user_id = _body["user"].get("id")
            self.channel_id = lookup.api.get_dm_channel_id(self.user_id)
            self.text = "dummy"

        _event = self.get_event_attribute(_body)
        self.user_id = _event.get("user", self.user_id)
        self.event_ts = _event.get("ts", self.event_ts)
        self.thread_ts = _event.get("thread_ts", self.thread_ts)
        self.channel_type = self.get_channel_type(_body)

        # スレッド内のポストか判定
        if float(self.thread_ts):
            self.in_thread = self.event_ts != self.thread_ts
        else:
            self.in_thread = False

        if "text" in _event:
            self.text = _event.get("text")
            if self.text:  # 空文字以外はキーワードと引数に分割
                self.keyword = self.text.split()[0]
                self.argument = self.text.split()[1:]
        else:  # text属性が見つからないときはログに出力
            if not _event.get("text") and not _body.get("type") == "block_actions":
                logging.error("text not found: %s", _body)

        self.check_updatable()

    def get_event_attribute(self, _body: dict) -> dict:
        """レスポンスからevent属性を探索して返す

        Args:
            _body (dict): レスポンス内容

        Returns:
            dict: event属性
        """

        _event: dict = {}

        if _body.get("command") == g.cfg.setting.slash_command:
            _event = _body

        if _body.get("event"):
            if not self.channel_id:
                if _body.get("channel_name") != "directmessage":
                    self.channel_id = _body["event"].get("channel")
                else:
                    self.channel_id = lookup.api.get_dm_channel_id(_body.get("user_id", ""))

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
                    logging.info("unknown subtype: %s", _body)

        return (_event)

    def get_channel_type(self, _body: dict) -> str | None:
        """レスポンスからchannel_typeを探索して返す

        Args:
            _body (dict): レスポンス内容

        Returns:
            str | None: channel_type
        """

        _channel_type: str | None = None

        if _body.get("command") == g.cfg.setting.slash_command:
            if _body.get("channel_name") == "directmessage":
                _channel_type = "im"
            else:
                _channel_type = "channel"
        else:
            if _body.get("event"):
                _channel_type = _body["event"].get("channel_type")

        return (_channel_type)

    def check_updatable(self):
        """DB更新可能チャンネルのポストかチェックする"""
        self.updatable = False

        if len(g.cfg.db.channel_limitations):
            if self.channel_id in g.cfg.db.channel_limitations.split(","):
                self.updatable = True
        else:
            match self.channel_type:
                case "channel":  # public channel
                    self.updatable = True
                case "group":  # private channel
                    self.updatable = True
                case "im":  # direct message
                    self.updatable = False
                case "search_messages":
                    self.updatable = True  # ToDo: channel_limitationsのチェックを入れる
