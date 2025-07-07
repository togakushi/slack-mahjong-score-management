"""
integrations/factory.py
"""

from integrations.base.message import MessageInterface
from integrations.standard_out.message import StandardOutMessage
from integrations.slack.message import SlackMessage


def get_message_adapter(selected_service: str) -> MessageInterface:
    """メッセージインターフェース"""

    if selected_service == "slack":
        return SlackMessage()
    else:
        return StandardOutMessage()
