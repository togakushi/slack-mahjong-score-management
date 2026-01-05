"""
integrations/standard_io/config.py
"""

import logging
from dataclasses import dataclass

from cls.config import BaseSection
from integrations.base.interface import IntegrationsConfig


@dataclass
class SvcConfig(BaseSection, IntegrationsConfig):
    """標準出力用個別設定値"""

    def __post_init__(self):
        assert self.main_conf
        self._parser = self.main_conf
        super().__init__(self, "standard_io")
        logging.debug("standard_io: %s", self)
