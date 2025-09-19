"""モジュール間データ共有用"""

from typing import TYPE_CHECKING, Any, Callable, Literal, Union

if TYPE_CHECKING:
    from argparse import Namespace

    from cls.config import AppConfig
    from cls.types import TeamDataDict
    from integrations.slack.config import AppConfig as slack_conf
    from integrations.standard_io.config import AppConfig as stdio_conf
    from integrations.web.config import AppConfig as web_conf

selected_service: Literal["slack", "web", "standard_io"] = "slack"
app_config: Union["slack_conf", "web_conf", "stdio_conf"]

args: "Namespace"
"""コマンドライン引数"""

slash_command_name: str
"""スラッシュコマンド名"""
slash_commands: dict[str, Callable[..., Any]] = {}
"""スラッシュコマンド用ディスパッチテーブル"""
special_commands: dict[str, Callable[..., Any]] = {}
"""個別コマンド用ディスパッチテーブル"""

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
