"""
integrations/standard_io/config.py
"""

from dataclasses import dataclass

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """標準出力用個別設定値"""

    def __post_init__(self):
        if self._parser is None:
            raise TypeError("Configuration file not specified.")

        self.read_file(parser=self._parser, selected_service="standard_io")
