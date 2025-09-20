"""モジュール間データ共有用"""

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from argparse import Namespace

    from cls.config import AppConfig
    from cls.types import AppConfigType, TeamDataDict

selected_service: Literal["slack", "web", "standard_io"] = "slack"
app_config: "AppConfigType"

args: "Namespace"
"""コマンドライン引数"""

# モジュール共通インスタンス
cfg: "AppConfig"
"""Configインスタンス共有"""

# 環境パラメータ
member_list: dict = {}
"""メンバーリスト
- 別名: 表示名
"""
team_list: list["TeamDataDict"] = []
"""チームリスト
- id: チームID
- team: チーム名
- member: 所属メンバーリスト
"""

params: dict = {}
"""プレースホルダ用パラメータ"""
