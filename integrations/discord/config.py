"""
integrations/discord/config.py
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from integrations.base.interface import IntegrationsConfig

if TYPE_CHECKING:
    from discord import ClientUser, Message


@dataclass
class SvcConfig(IntegrationsConfig):
    """discord用個別設定値"""

    bot_id: Optional["ClientUser"] = field(default=None)
    """ボットID"""

    # discord object
    response: Optional["Message"] = field(default=None)

    def __post_init__(self):
        self.read_file("discord")
