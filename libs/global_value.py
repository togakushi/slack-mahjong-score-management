"""モジュール間データ共有用"""

from typing import TYPE_CHECKING, Any, Callable, Literal, Union

if TYPE_CHECKING:
    from argparse import Namespace

    from cls.config import AppConfig
    from integrations.slack.adapter import ServiceAdapter as slack_adapter
    from integrations.standard_io.adapter import ServiceAdapter as std_adapter
    from integrations.web.adapter import ServiceAdapter as web_adapter
    from libs.types import TeamDataDict

# --- グローバル変数 ---
selected_service: Literal["slack", "web", "standard_io"] = "slack"
"""連携先サービス"""
adapter: Union["slack_adapter", "web_adapter", "std_adapter"]
"""インターフェースアダプタ"""

keyword_dispatcher: dict[str, Callable[..., Any]] = {}
"""キーワード呼び出しディスパッチテーブル"""
command_dispatcher: dict[str, Callable[..., Any]] = {}
"""スラッシュコマンドディスパッチテーブル"""

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
