"""モジュール間データ共有用"""

from typing import TYPE_CHECKING, Any, Callable, Literal

if TYPE_CHECKING:
    from argparse import Namespace

    from cls.config import AppConfig
    from cls.types import TeamDataDict
    from integrations.factory import AdapterType


selected_service: Literal["slack", "web", "standard_io"] = "slack"
"""選択サービス"""
adapter: "AdapterType"
"""インターフェースアダプタ"""

keyword_dispatcher: dict[str, Callable[..., Any]] = {}
"""キーワード呼び出しディスパッチャー"""
command_dispatcher: dict[str, Callable[..., Any]] = {}
"""スラッシュコマンドディスパッチャー"""

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
