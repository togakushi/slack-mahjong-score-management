"""モジュール間データ共有用"""

from typing import TYPE_CHECKING, Any, Callable, Literal, Union
from integrations.slack.adapter import ServiceAdapter as slack_adapter
from integrations.standard_io.adapter import ServiceAdapter as std_adapter
from integrations.web.adapter import ServiceAdapter as web_adapter

if TYPE_CHECKING:
    from argparse import Namespace

    from cls.config import AppConfig
    from cls.types import TeamDataDict

selected_service: Literal["slack", "web", "standard_io"] = "slack"
"""選択サービス"""
adapter: Union[slack_adapter, web_adapter, std_adapter]
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
