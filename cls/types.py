"""
cls/types.py
"""

from collections.abc import Mapping
from configparser import ConfigParser
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import (TYPE_CHECKING, Any, Callable, Literal, Tuple, TypedDict,
                    Union)

if TYPE_CHECKING:
    from cls.timekit import ExtendedDatetime


class GameInfoDict(TypedDict):
    """ゲーム集計情報格納辞書

    Attributes:
        game_count (int): ゲーム数
        first_game  (ExtendedDatetime): 記録されている最初のゲーム時間("%Y/%m/%d %H:%M:%S")
        last_game (ExtendedDatetime): 記録されている最後のゲーム時間("%Y/%m/%d %H:%M:%S")
        first_comment (str | None): 記録されている最初のゲームコメント
        last_comment (str | None): 記録されている最後のゲームコメント
    """

    game_count: int
    first_game: "ExtendedDatetime"
    last_game: "ExtendedDatetime"
    first_comment: str | None
    last_comment: str | None


class ComparisonDict(TypedDict, total=False):
    """メモ突合用辞書

    Attributes:
        mismatch (str): 差分
        missing (str): 追加
        delete (str): 削除
        remark_mod (str): 追加/削除
        remark_del (str): 削除
        invalid_score (str): 素点合計不一致
        pending (list[str]): 保留
    """

    mismatch: str
    missing: str
    delete: str
    remark_mod: str
    remark_del: str
    invalid_score: str
    pending: list[str]


class SlackSearchData(TypedDict, total=False):
    """slack検索結果格納辞書

    Attributes:
        text (str): 本文
        channel_id (str): チャンネルID
        user_id (str): ホストしたユーザID
        event_ts (str | None): ポスト時間
        thread_ts (str | None): スレッド元時間
        edited_ts (str | None): 最終編集時間
        reaction_ok (list): botが付けたOKリアクション
        reaction_ng (list): botが付けたNGリアクション
        in_thread (bool): スレッド内のポストか判定
        score (list): 本文がスコア報告ならパースした結果
        remarks (list): 本文がメモなら名前と内容のタプルのリスト
    """

    text: str
    """検索にヒットした本文の内容"""
    channel_id: str
    """見つけたチャンネルID"""
    user_id: str
    """投稿者のユーザID"""
    event_ts: str | None
    """ポストされた時間"""
    thread_ts: str | None
    """スレッドになっている場合、スレッド元の時間"""
    edited_ts: str | None
    """最後に編集された時間"""
    reaction_ok: list
    """botが付けたOKリアクション"""
    reaction_ng: list
    """botが付けたNGリアクション"""
    in_thread: bool
    """スレッドになっていればTrue(スレッド元は除く)"""
    score: list
    """スコア報告なら結果"""
    remarks: list
    """メモならその内容"""


class DateRangeSpec(TypedDict):
    """日付範囲変換キーワード用辞書"""
    keyword: list[str]
    range: Callable[[Any], list[datetime]]


class RankTableDict(TypedDict):
    """昇段ポイント計算テーブル用辞書"""
    grade: str
    point: list
    acquisition: list


class GradeTableDict(TypedDict, total=False):
    """段位テーブル用辞書"""
    name: str
    addition_expression: str
    table: list[RankTableDict]


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
                if x.name == "delete":
                    for data in config.get(section, "del", fallback="").split(","):
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
        ret_dict.update(format=getattr(self, "format", ""))
        ret_dict.update(filename=getattr(self, "filename", ""))
        ret_dict.update(interval=getattr(self, "interval", 80))

        drop_keys: list = [
            "config",
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
                return ret

        raise AttributeError(f"{attr} has no default or does not exist.")


@dataclass
class ParsedCommand:
    """コマンド解析結果"""
    flags: dict[str, Any]
    arguments: list[str]
    unknown: list[str]
    search_range: list["ExtendedDatetime"]


# CommandParser用
CommandResult = Mapping[str, Union[str, int, bool, Tuple[str, ...]]]
CommandAction = Callable[[Union[str, Tuple[str, ...]]], CommandResult]


class CommandSpec(TypedDict, total=False):
    """コマンドマッピング"""
    match: list[str]
    action: CommandAction
    type: Literal["int", "str", "sql", "filename"]
