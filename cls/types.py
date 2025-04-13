"""
cls/types.py
"""

from configparser import ConfigParser
from dataclasses import asdict, dataclass, fields
from typing import Any, TypedDict, Union


class GameInfoDict(TypedDict, total=False):
    """ゲーム集計情報格納辞書"""
    game_count: int
    first_game: str
    last_game: str
    first_comment: str | None
    last_comment: str | None


class ComparisonDict(TypedDict, total=False):
    """メモ突合用辞書"""
    mismatch: str
    missing: str
    delete: str
    remark_mod: str
    remark_del: str
    invalid_score: str
    pending: list[str]


class SlackSearchDict(TypedDict, total=False):
    """slack検索結果格納辞書"""
    event_ts: str | None
    thread_ts: str | None
    edited_ts: str | None
    reaction_ok: list
    reaction_ng: list
    in_thread: bool
    score: list
    remarks: list


@dataclass
class CommonMethodMixin:
    """データクラス共通メソッド"""
    def initialization(self, section: str | None = None) -> None:
        """設定ファイルから値を取りこみ"""
        config = getattr(self, "config")
        assert config is not None, "config must not be None"

        if section is None:
            section = getattr(self, "section")
        assert section is not None, "section must not be None"

        for x in fields(self):
            if x.type == Union[ConfigParser | None]:
                continue
            if x.type == Union[str | None] and x.name == "section":
                setattr(self, x.name, section)
            elif x.type == bool:
                setattr(self, x.name, config.getboolean(section, x.name, fallback=x.default))
            elif x.type == str:
                setattr(self, x.name, config.get(section, x.name, fallback=x.default))
            elif x.type == int:
                setattr(self, x.name, config.getint(section, x.name, fallback=x.default))
            elif x.type == float:
                setattr(self, x.name, config.getfloat(section, x.name, fallback=x.default))
            elif x.type == list:
                tmp_list: list = []
                for data in config.get(section, x.name, fallback="").split(","):
                    tmp_list.extend(data.split())
                setattr(self, x.name, tmp_list)
            else:
                setattr(self, x.name, config.get(section, x.name, fallback=x.default))

        # 共通パラメータ初期化
        self.format = str()
        self.filename = str()
        self.aggregate_unit = str()
        self.interval = 80

    def to_dict(self) -> dict:
        """必要なパラメータを辞書型で返す

        Returns:
            dict: 返却値
        """

        ret_dict: dict = asdict(self)

        drop_keys: list = [
            "config",
            "section",
            "always_argument",
            "search_range",
        ]

        for key in drop_keys:
            if key in ret_dict:
                ret_dict.pop(key)

        return (ret_dict)

    def get_default(self, attr: str) -> Any:
        """デフォルト値を取得して返す

        Args:
            attr (str): 属性

        Raises:
            AttributeError: 未定義

        Returns:
            Any: デフォルト値
        """

        ret: Any

        for x in fields(self):
            if x.name == attr:
                config = getattr(self, "config")
                assert config is not None, "config must not be None"
                section = getattr(self, "section")
                assert section is not None, "section must not be None"

                if x.type == Union[str | None]:
                    ret = None
                elif x.type == bool:
                    ret = config.getboolean(section, x.name, fallback=x.default)
                elif x.type == str:
                    ret = config.get(section, x.name, fallback=x.default)
                elif x.type == int:
                    ret = config.getint(section, x.name, fallback=x.default)
                elif x.type == float:
                    ret = config.getfloat(section, x.name, fallback=x.default)
                elif x.type == list:
                    ret = []
                else:
                    ret = config.get(section, x.name, fallback=x.default)
                return (ret)

        raise AttributeError(f"{attr} has no default or does not exist.")
