"""
tests/events/test_integrations_web.py
"""

import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask
from flask_httpauth import HTTPBasicAuth  # type: ignore

import libs.global_value as g
from integrations import factory
from integrations.web.events import create_bp
from libs import configuration


@pytest.fixture(scope="module", autouse=True)
def patch_by_keyword():
    """libs.dispatcher.by_keyword を全テストでモック"""
    with patch("libs.dispatcher.by_keyword") as mock_by_keyword:
        mock_by_keyword.return_value = None
        yield mock_by_keyword


@pytest.fixture(name="flask_client")
def client(request):
    """Flask テストクライアント"""
    config_path = request.param
    sys.argv = ["app.py", "--service=web", f"--config=tests/testdata/{config_path}"]
    configuration.setup(init_db=False)

    adapter = factory.select_adapter("web", g.cfg)

    app = Flask(
        __name__,
        static_folder=os.path.join(g.cfg.script_dir, "files/html/static"),
        template_folder=os.path.join(g.cfg.script_dir, "files/html/template"),
    )

    app.config["TESTING"] = True
    app.config["padding"] = "0.25em 1.5em"
    app.config["players"] = []
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

    with app.test_client() as test_client:
        yield test_client


@pytest.mark.parametrize(
    "flask_client, url, expected_status",
    [
        ("minimal.ini", "/", 200),
        ("minimal.ini", "/summary/", 200),
        ("minimal.ini", "/graph/", 200),
        ("minimal.ini", "/ranking/", 200),
        ("minimal.ini", "/detail/", 200),
        ("minimal.ini", "/report/", 200),
        ("minimal.ini", "/score/", 403),
        ("minimal.ini", "/member/", 403),
        ("minimal.ini", "/unknown/", 404),
        ("minimal.ini", "/static/stylesheet.css", 200),
        ("minimal.ini", "/static/unknown.css", 404),
        ("minimal.ini", "/user_static/user.css", 403),
        ("minimal.ini", "/user_static/config.ini", 403),
        ("web_customize.ini", "/", 200),
        ("web_customize.ini", "/summary/", 403),
        ("web_customize.ini", "/graph/", 403),
        ("web_customize.ini", "/ranking/", 403),
        ("web_customize.ini", "/detail/", 403),
        ("web_customize.ini", "/report/", 200),
        ("web_customize.ini", "/member/", 200),
        ("web_customize.ini", "/score/", 200),
        ("web_customize.ini", "/static/stylesheet.css", 200),
        ("web_customize.ini", "/static/unknown.css", 404),
        ("web_customize.ini", "/user_static/user.css", 200),
        ("web_customize.ini", "/user_static/config.ini", 403),
        ("web_with_auth.ini", "/", 401),
        ("web_with_auth.ini", "/summary/", 401),
        ("web_with_auth.ini", "/graph/", 401),
        ("web_with_auth.ini", "/ranking/", 401),
        ("web_with_auth.ini", "/detail/", 401),
        ("web_with_auth.ini", "/report/", 401),
        ("web_with_auth.ini", "/member/", 401),
        ("web_with_auth.ini", "/score/", 401),
        ("web_with_auth.ini", "/static/stylesheet.css", 401),
        ("web_with_auth.ini", "/static/unknown.css", 401),
        ("web_with_auth.ini", "/user_static/user.css", 401),
        ("web_with_auth.ini", "/user_static/config.ini", 401),
    ],
    indirect=["flask_client"],
)
def test_route_access(flask_client, url, expected_status):
    """ルート選択テスト"""
    print("-->", url)

    response = flask_client.get(url)
    assert response.status_code == expected_status
