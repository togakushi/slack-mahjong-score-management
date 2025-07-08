from integrations.base.interface import MessageParserInterface


class MessageParser(MessageParserInterface):
    def parser(self, _body: dict):
        _ = _body

    def check_updatable(self):
        pass
