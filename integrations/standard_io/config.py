"""
integrations/slack/config.py
"""

from dataclasses import dataclass

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """設定値"""
