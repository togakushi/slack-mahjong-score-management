"""
integrations/standard_io/config.py
"""

from dataclasses import dataclass

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """標準出力用個別設定値"""

    def __post_init__(self):
        self.read_file("standard_io")
