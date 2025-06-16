"""
cls/subcom.py
"""

from configparser import ConfigParser
from dataclasses import dataclass, field
from math import ceil

from cls.types import CommonMethodMixin


@dataclass
class SubCommand(CommonMethodMixin):
    """サブコマンド共通デフォルト値"""
    _config: ConfigParser | None = None
    section: str | None = None
    aggregation_range: str = field(default="当日")
    """検索範囲未指定時に使用される範囲"""
    individual: bool = field(default=True)
    """個人/チーム集計切替フラグ
    - True: 個人集計
    - False: チーム集計
    """
    all_player: bool = field(default=False)
    daily: bool = field(default=True)
    fourfold: bool = field(default=True)
    game_results: bool = field(default=False)
    guest_skip: bool = field(default=True)
    guest_skip2: bool = field(default=True)
    ranked: int = field(default=3)
    score_comparisons: bool = field(default=False)
    """スコア比較"""
    statistics: bool = field(default=False)
    """統計情報表示"""
    stipulated: int = field(default=1)
    """規定打数指定"""
    stipulated_rate: float = field(default=0.05)
    """規定打数計算レート"""
    unregistered_replace: bool = field(default=True)
    """メンバー未登録プレイヤー名をゲストに置き換えるかフラグ
    - True: 置き換える
    - False: 置き換えない
    """
    anonymous: bool = field(default=False)
    """匿名化フラグ"""
    verbose: bool = field(default=False)
    """詳細情報出力フラグ"""
    versus_matrix: bool = field(default=False)
    """対戦マトリックス表示"""
    collection: str = field(default=str())
    search_word: str = field(default=str())
    group_length: int = field(default=0)
    always_argument: list = field(default_factory=list)
    """オプションとして常に付与される文字列(カンマ区切り)"""

    def __post_init__(self):
        self.initialization(self.section)

    def stipulated_calculation(self, game_count: int) -> int:
        """規定打数をゲーム数から計算

        Args:
            game_count (int): 指定ゲーム数

        Returns:
            int: 規定ゲーム数
        """

        return int(ceil(game_count * self.stipulated_rate) + 1)
