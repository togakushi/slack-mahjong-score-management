"""
integrations/factory.py
"""

from integrations.base.adapter import APIInterface
from integrations.standard_out.adapter import StandardOut
from integrations.slack.adapter import SlackAPI


def get_api_adapter(selected_service: str) -> APIInterface:
    """メッセージインターフェース"""

    if selected_service == "slack":
        return SlackAPI()
    else:
        return StandardOut()
