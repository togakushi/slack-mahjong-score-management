"""
integrations/standard_io/config.py
"""

from configparser import ConfigParser
from dataclasses import dataclass, field

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """標準出力用個別設定値"""

    _parser: ConfigParser | None = field(default=None)
    """設定ファイル"""

    def __post_init__(self):
        if self._parser is None:
            raise TypeError("")

        self.read_file(parser=self._parser, selected_service="standard_io")
