"""
integrations/slack/parser.py
"""

import logging
from typing import TYPE_CHECKING, cast

import libs.global_value as g
from integrations.base.interface import MessageParserDataMixin, MessageParserInterface
from integrations.protocols import MsgData, PostData, StatusData

if TYPE_CHECKING:
    from integrations.slack.adapter import ServiceAdapter


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    def __init__(self):
        MessageParserDataMixin.__init__(self)
        self.data: MsgData = MsgData()
        self.post: PostData = PostData()
        self.status: StatusData = StatusData()

    def parser(self, _body: dict):
        g.adapter = cast("ServiceAdapter", g.adapter)
        _event = cast(dict, _body.get("event", _body))  # 対象のevent抽出

        if _body.get("command") == g.adapter.conf.slash_command:  # スラッシュコマンド
            self.status.command_flg = True
            self.status.command_name = g.adapter.conf.slash_command
            self.data.user_id = str(_body.get("user_id", ""))
            if _body.get("channel_name") == "directmessage":
                self.data.channel_type = "im"
                self.data.status = "message_append"
                self.data.channel_id = str(_body.get("channel_id", ""))
            else:  # チャンネル内コマンド
                self.data.channel_type = "im"
                self.data.channel_id = g.adapter.functions.get_dm_channel_id(self.data.user_id)  # DM Open
        elif _body.get("container"):  # Homeタブ
            self.data.user_id = str(cast(dict, _body["user"]).get("id", ""))
            self.data.channel_id = g.adapter.functions.get_dm_channel_id(self.data.user_id)
            self.data.channel_type = "channel"
            self.data.text = "dummy"
        elif _body.get("iid"):  # 検索結果
            if _channel_id := str(cast(dict, _event["channel"]).get("id", "")):
                self.data.channel_id = _channel_id
                _event.pop("channel")
            self.data.channel_type = "search_messages"
            self.data.status = "message_append"
        else:
            match _event.get("subtype"):
                case subtype if str(subtype).endswith(("_topic", "_purpose", "_name")):
                    self.data.status = "do_nothing"
                    return
                case "message_changed":
                    self.data.status = "message_changed"
                    _event.update(cast(dict, _event["message"]))
                    if cast(dict, _event["message"]).get("subtype") == "tombstone":  # スレッド元の削除
                        self.data.status = "message_deleted"
                    elif _edited := cast(dict, _event["message"]).get("edited"):
                        self.data.edited_ts = str(cast(dict, _edited).get("ts", "undetermined"))
                    if _previous_message := cast(dict, _event.get("previous_message", {})):
                        if _previous_message.get("thread_ts"):
                            _event.update(thread_ts=_previous_message.get("thread_ts", "0"))
                        if cast(dict, _event["message"]).get("text") == _previous_message.get("text"):
                            self.data.status = "do_nothing"
                case "message_deleted":
                    self.data.status = "message_deleted"
                    _event.update(cast(dict, _event["previous_message"]))
                case "file_share" | "thread_broadcast":
                    self.data.status = "message_append"
                case None:
                    self.data.status = "message_append"
                case _:
                    self.data.status = "message_append"
                    logging.warning("unknown subtype: %s", _body)

        self.data.text = _event.get("text", self.data.text)
        self.data.channel_id = _event.get("channel", self.data.channel_id)
        self.data.channel_type = _event.get("channel_type", self.data.channel_type)
        self.data.user_id = _event.get("user", self.data.user_id)
        self.data.event_ts = _event.get("ts", "0")
        self.data.thread_ts = _event.get("thread_ts", "0")
        self.status.source = f"slack_{self.data.channel_id}"

        logging.debug(self.data)

    @property
    def in_thread(self) -> bool:
        """スレッド内のメッセージか判定"""
        if self.data.thread_ts == "0":
            return False
        if self.data.event_ts == self.data.thread_ts:
            return False
        return True

    @property
    def is_bot(self) -> bool:
        if self.data.user_id == "USLACKBOT":
            return True
        return False

    @property
    def check_updatable(self) -> bool:
        g.adapter = cast("ServiceAdapter", g.adapter)
        ret: bool = False

        # 突合処理中はチェック省略
        if self.status.command_type == "comparison":
            return True

        if g.adapter.conf.channel_limitations:
            if self.data.channel_id in g.adapter.conf.channel_limitations:
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

    @property
    def ignore_user(self) -> bool:
        g.adapter = cast("ServiceAdapter", g.adapter)
        return self.data.user_id in g.adapter.conf.ignore_userid
