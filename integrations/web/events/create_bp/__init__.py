"""
ルート設定
"""

from integrations.web.events.create_bp.detail import detail_bp
from integrations.web.events.create_bp.graph import graph_bp
from integrations.web.events.create_bp.index import index_bp
from integrations.web.events.create_bp.member import member_bp
from integrations.web.events.create_bp.ranking import ranking_bp
from integrations.web.events.create_bp.report import report_bp
from integrations.web.events.create_bp.score import score_bp
from integrations.web.events.create_bp.summary import summary_bp
from integrations.web.events.create_bp.user_assets import user_assets_bp

__all__ = [
    "detail_bp",
    "graph_bp",
    "index_bp",
    "member_bp",
    "ranking_bp",
    "report_bp",
    "score_bp",
    "summary_bp",
    "user_assets_bp",
]
