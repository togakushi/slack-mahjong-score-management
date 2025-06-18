"""
cls/mixin.py
"""

from configparser import ConfigParser
from dataclasses import asdict, dataclass, fields
from typing import Any, Union, cast


@dataclass
class CommonMethodMixin:
    """データクラス共通メソッド"""
    def initialization(self, section: str | None = None) -> None:
        """設定ファイルから値を取りこみ"""
        _config = cast(ConfigParser, getattr(self, "_config"))
        assert _config is not None, "config must not be None"

        if section is None:
            section = getattr(self, "section")
        assert section is not None, "section must not be None"

        for x in fields(self):
            if x.type == Union[ConfigParser | None]:
                continue
            if x.type == Union[str | None] and x.name == "section":
                setattr(self, x.name, section)
            elif x.type == bool:
                setattr(self, x.name, _config.getboolean(section, x.name, fallback=x.default))
            elif x.type == str:
                setattr(self, x.name, _config.get(section, x.name, fallback=x.default))
            elif x.type == int:
                setattr(self, x.name, _config.getint(section, x.name, fallback=x.default))
            elif x.type == float:
                setattr(self, x.name, _config.getfloat(section, x.name, fallback=x.default))
            elif x.type == list:
                tmp_list: list = []
                for data in _config.get(section, x.name, fallback="").split(","):
                    tmp_list.extend(data.split())
                if x.name == "delete":
                    for data in _config.get(section, "del", fallback="").split(","):
                        tmp_list.extend(data.split())
                setattr(self, x.name, tmp_list)
            else:
                setattr(self, x.name, _config.get(section, x.name, fallback=x.default))

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
        ret_dict.update(format=getattr(self, "format", ""))
        ret_dict.update(filename=getattr(self, "filename", ""))
        ret_dict.update(interval=getattr(self, "interval", 80))

        drop_keys: list = [
            "_config",
            "section",
            "always_argument",
            "regulations_type2",
            "rank_point",
        ]

        for key in drop_keys:
            if key in ret_dict:
                ret_dict.pop(key)

        return ret_dict

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
                _config = getattr(self, "_config")
                assert _config is not None, "config must not be None"
                section = getattr(self, "section")
                assert section is not None, "section must not be None"

                if x.type == Union[str | None]:
                    ret = None
                elif x.type == bool:
                    ret = _config.getboolean(section, x.name, fallback=x.default)
                elif x.type == str:
                    ret = _config.get(section, x.name, fallback=x.default)
                elif x.type == int:
                    ret = _config.getint(section, x.name, fallback=x.default)
                elif x.type == float:
                    ret = _config.getfloat(section, x.name, fallback=x.default)
                elif x.type == list:
                    ret = []
                else:
                    ret = _config.get(section, x.name, fallback=x.default)
                return ret

        raise AttributeError(f"{attr} has no default or does not exist.")
