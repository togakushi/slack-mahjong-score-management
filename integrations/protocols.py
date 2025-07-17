"""
integrations/protocols.py
"""

from typing import Any, Protocol

from integrations.base.interface import MsgData, PostData


class MessageParserProtocol(Protocol):
    data = MsgData()
    post = PostData()

    @property
    def in_thread(self) -> bool:
        ...

    @property
    def keyword(self) -> str:
        ...

    @property
    def argument(self) -> list:
        ...

    def get_score(self, keyword: str) -> dict:
        ...

    def get_remarks(self, keyword: str) -> list:
        ...

    def parser(self, body: Any):
        ...

    def check_updatable(self) -> bool:
        ...
