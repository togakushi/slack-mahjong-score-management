"""
integrations/slack/config.py
"""

from dataclasses import dataclass, field

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """設定値"""

    reaction_ok: str = field(default="ok")
    """DBに取り込んだ時に付けるリアクション"""
    reaction_ng: str = field(default="ng")
    """DBに取り込んだが正確な値ではない可能性があるときに付けるリアクション"""
