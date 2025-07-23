"""
integrations/slack/parser.py
"""

import logging
from typing import cast

import libs.global_value as g
from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.slack import adapter


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    def __init__(self, reaction_ok: str, reaction_ng: str):
        MessageParserDataMixin.__init__(self, reaction_ok, reaction_ng)

    def parser(self, _body: dict):
        api_adapter = adapter.SlackAPI()

        # 対象のevent抽出
        _event = cast(dict, _body.get("event", _body))

        if _body.get("command") == g.cfg.setting.slash_command:  # スラッシュコマンド
            if _body.get("channel_name") == "directmessage":
                self.data.channel_type = "im"
                self.data.channel_id = _body.get("channel_id", "")
            else:
                self.data.channel_id = api_adapter.lookup.get_dm_channel_id(_body.get("user_id", ""))
        elif _body.get("container"):  # Homeタブ
            self.data.user_id = _body["user"].get("id")
            self.data.channel_id = api_adapter.lookup.get_dm_channel_id(self.data.user_id)
            self.data.channel_type = "channel"
            self.data.text = "dummy"
        elif _body.get("iid"):  # 検索結果
            if (channel_id := str(cast(dict, _event["channel"]).get("id", ""))):
                self.data.channel_id = channel_id
                _event.pop("channel")
            self.data.channel_type = "search_messages"
            self.data.status = "message_append"
        else:
            match _event.get("subtype"):
                case "message_changed":
                    self.data.status = "message_changed"
                    _event.update(cast(dict, _event["message"]))
                    if (previous_message := cast(dict, _event.get("previous_message", {}))):
                        _event.update(thread_ts=previous_message.get("thread_ts", "0"))
                case "message_deleted":
                    self.data.status = "message_deleted"
                    _event.update(cast(dict, _event["previous_message"]))
                case "file_share":
                    self.data.status = "message_append"
                case None:
                    self.data.status = "message_append"
                case _:
                    self.data.status = "message_append"
                    logging.info("unknown subtype: %s", _body)

        self.data.text = _event.get("text", self.data.text)
        self.data.channel_id = _event.get("channel", self.data.channel_id)
        self.data.channel_type = _event.get("channel_type", self.data.channel_type)
        self.data.user_id = _event.get("user", self.data.user_id)
        self.data.event_ts = _event.get("ts", "0")
        self.data.thread_ts = _event.get("thread_ts", "0")

    @property
    def check_updatable(self) -> bool:
        """DB更新可能チャンネルのポストかチェックする"""
        ret: bool = True

        if g.cfg.db.channel_limitations:
            if self.data.channel_id in g.cfg.db.channel_limitations:
                ret = True
        else:  # リストが空なら全チャンネルが対象
            match self.data.channel_type:
                case "channel":  # public channel
                    ret = True
                case "group":  # private channel
                    ret = True
                case "im":  # direct message
                    ret = False
                case "search_messages":
                    ret = True

        return ret
