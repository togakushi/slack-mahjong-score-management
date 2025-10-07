"""
tests/events/test_integrations_web.py
"""

import os
import sys
from unittest.mock import patch

import pytest
from flask import Flask

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


@pytest.fixture
def client():
    """Flask テストクライアント"""
    sys.argv = ["app.py", "--service=web", "--config=tests/testdata/minimal.ini"]
    configuration.setup()
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

    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "url,expected_status",
    [
        ("/", 200),
        ("/summary/", 200),
        ("/graph/", 200),
        ("/ranking/", 200),
        ("/detail/", 200),
        ("/report/", 200),
        ("/score/", 403),
        ("/member/", 403),
        ("/unknown/", 404),
        ("static/stylesheet.css", 200),
        ("static/unknown.css", 404),
        ("/user_static/user.css", 403),
        ("/user_static/config.ini", 403),
    ],
)
def test_route_access(client, url, expected_status):
    print("-->", url)
    response = client.get(url)
    assert response.status_code == expected_status
