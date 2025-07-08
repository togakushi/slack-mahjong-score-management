from integrations.base.interface import MessageParserInterface


class MessageParser(MessageParserInterface):
    def parser(self):
        return super().parser()
