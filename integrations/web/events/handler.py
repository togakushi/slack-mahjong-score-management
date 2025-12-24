"""
integrations/web/events/handler.py
"""

import os
from typing import TYPE_CHECKING

from flask import Flask
from flask_httpauth import HTTPBasicAuth  # type: ignore

import libs.global_value as g
from integrations.web.events import create_bp

if TYPE_CHECKING:
    from integrations.web.adapter import ServiceAdapter


def main(adapter: "ServiceAdapter"):
    """メイン処理"""

    app = Flask(
        __name__,
        static_folder=os.path.join(g.cfg.script_dir, "files/html/static"),
        template_folder=os.path.join(g.cfg.script_dir, "files/html/template"),
    )

    app.config["padding"] = "0.25em 1.5em"
    app.config["players"] = g.cfg.member.lists
    app.register_blueprint(create_bp.index_bp(adapter))
    app.register_blueprint(create_bp.summary_bp(adapter))
    app.register_blueprint(create_bp.graph_bp(adapter))
    app.register_blueprint(create_bp.ranking_bp(adapter))
    app.register_blueprint(create_bp.detail_bp(adapter))
    app.register_blueprint(create_bp.report_bp(adapter))
    app.register_blueprint(create_bp.member_bp(adapter))
    app.register_blueprint(create_bp.score_bp(adapter))
    app.register_blueprint(create_bp.user_assets_bp(adapter))

    auth = HTTPBasicAuth()

    @auth.verify_password
    def verify_password(username, password):
        if username == adapter.conf.username and password == adapter.conf.password:
            return True
        return False

    @app.before_request
    def require_auth():
        if adapter.conf.require_auth:
            return auth.login_required(lambda: None)()
        return None

    if adapter.conf.use_ssl:
        if not os.path.exists(adapter.conf.certificate):
            raise FileNotFoundError("certificate file not found")
        if not os.path.exists(adapter.conf.private_key):
            raise FileNotFoundError("private key file not found")
        app.run(
            host=adapter.conf.host,
            port=adapter.conf.port,
            ssl_context=(adapter.conf.certificate, adapter.conf.private_key),
        )
    else:
        app.run(host=adapter.conf.host, port=adapter.conf.port)
