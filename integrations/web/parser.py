"""
integrations/web/parser.py
"""

from configparser import ConfigParser
from typing import cast

import libs.global_value as g
from integrations.base.interface import (MessageParserDataMixin,
                                         MessageParserInterface)
from integrations.protocols import MsgData, PostData
from integrations.web import config


class MessageParser(MessageParserDataMixin, MessageParserInterface):
    """メッセージ解析クラス"""

    conf = config.AppConfig
    data = MsgData
    post = PostData

    def __init__(self):
        self.conf = config.AppConfig()
        self.conf.read_file(cast(ConfigParser, getattr(g.cfg, "_parser")), g.selected_service)
        self.conf.initialization()
        self.data = MsgData()
        self.post = PostData()

    def parser(self, body: dict):
        _ = body

    @property
    def is_command(self) -> bool:
        return False

    @property
    def check_updatable(self) -> bool:
        return True
