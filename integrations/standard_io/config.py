"""
integrations/standard_io/config.py
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from cls.config import BaseSection
from integrations.base.interface import IntegrationsConfig

if TYPE_CHECKING:
    from pathlib import Path  # noqa: F401


@dataclass
class SvcConfig(BaseSection, IntegrationsConfig):
    """標準出力用個別設定値"""

    def __post_init__(self):
        assert self.main_conf
        self._parser = self.main_conf
        super().__init__(self, "standard_io")
        logging.debug("standard_io: %s", self)
