"""
cls/subcom.py
"""

from configparser import ConfigParser
from dataclasses import dataclass, field, fields
from math import ceil

from cls.types import CommonMethodMixin
from libs.data import lookup
from libs.functions.search import search_range
from libs.utils import dictutil, formatter


@dataclass
class SubCommand(CommonMethodMixin):
    """サブコマンド共通デフォルト値"""
    config: ConfigParser | None = None
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
    game_results: str | bool = field(default=False)
    guest_skip: bool = field(default=True)
    guest_skip2: bool = field(default=True)
    ranked: int = field(default=3)
    score_comparisons: bool = field(default=False)
    statistics: bool = field(default=False)
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
    verbose: bool = field(default=False)
    versus_matrix: bool = field(default=False)
    collection: str = field(default=str())
    search_word: str = field(default=str())
    group_length: int = field(default=0)
    always_argument: list = field(default_factory=list)

    def __post_init__(self):
        self.initialization(self.section)

    def update(self, argument: list) -> dict:
        """引数を解析し、パラメータの更新、集計範囲のパラメータを返す

        Args:
            argument (list): 引数

        Returns:
            dict: 集計範囲パラメータ
            - player_name: str
            - search_range: []
            - player_list: []
            - competition_list: []
        """

        self.initialization(self.section)
        ret_dict: dict = {
            "player_name": "",
            "search_range": [],
            "player_list": [],
            "competition_list": [],
        }
        new_flag: dict = {}
        tmp_range: list = []

        # 引数解析
        new_flag = dictutil.analysis_argument(self.always_argument)
        if new_flag["search_range"]:
            tmp_range = new_flag["search_range"]
        else:
            tmp_range.append(self.aggregation_range)
        self.update_from_dict(new_flag)

        new_flag = dictutil.analysis_argument(argument)
        if new_flag["search_range"]:
            tmp_range = new_flag["search_range"]
        self.update_from_dict(new_flag)

        ret_dict.update(search_range=search_range(tmp_range))

        if new_flag.get("interval"):
            ret_dict.update(interval=new_flag.get("interval"))
        if new_flag.get("format"):
            ret_dict.update(format=new_flag.get("format"))
        if new_flag.get("filename"):
            ret_dict.update(filename=new_flag.get("filename"))

        # どのオプションにも該当しないキーワードはプレイヤー名 or チーム名
        player_name: str = str()
        target_player: list = []
        player_list: dict = {}
        competition_list: dict = {}
        team_list: list = lookup.internal.get_team()

        for x in new_flag["unknown_command"]:
            if x in team_list:
                target_player.append(x)
            elif self.individual and self.unregistered_replace:
                target_player.append(formatter.name_replace(x))
            else:
                target_player.append(x)

        if target_player:
            player_name = target_player[0]

        if self.all_player:  # 全員追加
            target_player = list(set(lookup.internal.get_member() + target_player))
        else:
            target_player = list(set(target_player))

        # リスト生成
        for idx, name in enumerate(target_player):
            player_list[f"player_{idx}"] = name
            competition_list[f"competition_{idx}"] = name

        for delete_key in [k for k, v in competition_list.items() if v == player_name]:
            del competition_list[delete_key]

        ret_dict.update(player_name=player_name)
        ret_dict.update(target_player=target_player)
        ret_dict.update(player_list=player_list)
        ret_dict.update(competition_list=competition_list)

        return (ret_dict)

    def stipulated_calculation(self, game_count: int) -> int:
        """規定打数をゲーム数から計算

        Args:
            game_count (int): 指定ゲーム数

        Returns:
            int: 規定ゲーム数
        """

        return int(ceil(game_count * self.stipulated_rate) + 1)

    def update_from_dict(self, update_dict: dict) -> None:
        """辞書による値の更新

        Args:
            update_dict (dict): 更新するデータ
        """

        for x in fields(self):
            if x.name in update_dict:
                setattr(self, x.name, update_dict[x.name])
