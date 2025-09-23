"""
integrations/web/config.py
"""

import os
from dataclasses import dataclass, field

import libs.global_value as g
from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """WebUI用個別設定値"""

    host: str = field(default="")
    """起動アドレス(未指定はコマンドライン引数デフォルト値)"""
    port: int = field(default=0)
    """起動ポート(未指定はコマンドライン引数デフォルト値)"""

    # 認証
    require_auth: bool = field(default=False)
    """BASIC認証を利用するか"""
    username: str = field(default="")
    """認証ユーザ名"""
    password: str = field(default="")
    """認証パスワード"""

    # 暗号
    use_ssl: bool = field(default=False)
    """HTTPSを有効にするか"""
    certificate: str = field(default="")
    """サーバー証明書パス"""
    private_key: str = field(default="")
    """秘密鍵パス"""

    # 表示オプション
    view_summary: bool = field(default=True)
    """成績サマリ/個人成績の表示"""
    view_graph: bool = field(default=True)
    """グラフの表示"""
    view_ranking: bool = field(default=True)
    """ランキングの表示"""
    management_member: bool = field(default=False)
    """メンバー/チーム編集メニューの表示"""
    management_score: bool = field(default=False)
    """成績管理メニューの表示"""
    custom_css: str = field(default="")
    """ユーザー指定CSSファイル"""

    plotting_backend: str = field(default="plotly")

    def initialization(self):
        """初期化処理"""

        if not self.host:
            self.host = g.args.host

        if not self.port:
            self.port = g.args.port

        if not all([self.username, self.password]):
            self.require_auth = False

        if not all([self.private_key, self.certificate]):
            self.use_ssl = False

        if not os.path.isfile(os.path.join(g.cfg.config_dir, self.custom_css)):
            self.custom_css = ""
