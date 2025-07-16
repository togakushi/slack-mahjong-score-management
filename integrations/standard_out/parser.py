from typing import cast

from integrations.base.interface import MessageParserInterface


class MessageParser(MessageParserInterface):
    def __init__(self):
        super().__init__()

    def parser(self, body: dict):
        self.data.channel_id = "dummy"
        if body.get("event"):
            body = cast(dict, body["event"])

        if body.get("text"):
            self.data.text = str(body.get("text", ""))
        else:
            self.data.text = ""

    @property
    def check_updatable(self) -> bool:
        return True
