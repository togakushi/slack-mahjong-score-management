"""
integrations/web/config.py
"""

from dataclasses import dataclass, field

import libs.global_value as g
from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """設定値"""
    host: str = field(default="")
    port: int = field(default=0)

    require_auth: bool = field(default=False)
    username: str = field(default="")
    password: str = field(default="")

    use_ssl: bool = field(default=False)
    certificate: str = field(default="")
    private_key: str = field(default="")

    view_summary: bool = field(default=True)
    view_graph: bool = field(default=True)
    view_ranking: bool = field(default=True)
    management_member: bool = field(default=False)
    management_score: bool = field(default=False)

    def initialization(self):
        """初期化"""

        if not self.host:
            self.host = g.args.host

        if not self.port:
            self.port = g.args.port

        if not all([self.username, self.password]):
            self.require_auth = False

        if not all([self.private_key, self.certificate]):
            self.use_ssl = False
