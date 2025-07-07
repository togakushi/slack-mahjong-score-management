"""
integrations/factory.py
"""

from integrations.base.adapter import APIInterface
from integrations.standard_out.adapter import StandardOut
from integrations.slack.adapter import SlackAPI


def get_api_adapter(selected_service: str) -> APIInterface:
    """メッセージインターフェース"""

    match selected_service:
        case "slack":
            return SlackAPI()
        case _:
            return StandardOut()
