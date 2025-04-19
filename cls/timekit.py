"""
timekit - datetime 拡張ユーティリティ

- ExtendedDatetime: 柔軟な初期化と書式変換ができる datetime ラッパー
"""

from datetime import datetime
from typing import Literal, TypeAlias, Union

from dateutil.relativedelta import relativedelta

__all__ = ["ExtendedDatetime"]


class ExtendedDatetime:
    """datetime拡張ラップクラス

    Examples:
        >>> from cls.timekit import ExtendedDatetime
        >>> t = ExtendedDatetime("2025-04-19 12:34:56")
        >>> t.format("ymdhm")
        '2025/04/19 12:34'

        >>> t.set("2025-05-01 00:00:00")
        >>> t.format("sql")
        '2025-05-01 00:00:00.000000'

        >>> from dateutil.relativedelta import relativedelta
        >>> t2 = t + relativedelta(days=93)
        >>> t2.format("ymd")
        '2025/08/02'

        >>> t + {"days": 1, "months": 2}
        2025-07-02 00:00:00.000000
    """

    _dt: datetime
    """操作対象"""

    # 型アノテーション用定数
    AcceptedTypes: TypeAlias = Union[str, float, datetime, "ExtendedDatetime"]
    """引数として受け付ける型
    - **str**: 日付文字列（ISO形式など）
    - **float**: UNIXタイムスタンプ
    - **datetime** / **ExtendedDatetime**: オブジェクトをそのまま利用
    """

    FormatType: TypeAlias = Literal[
        "ts", "y", "ym", "ymd", "ymdhm", "ymdhms", "hm", "hms",
        "sql", "ext",
    ]
    """フォーマット変換で指定する種類
    - **ts**: タイムスタンプ
    - **y**: %Y
    - **ym**: %Y/%m
    - **ymd**: %Y/%m/%d
    - **ymdhm**: %Y/%m/%d %H:%M
    - **ymdhms**: %Y/%m/%d %H:%M:%S
    - **hm**: %H:%M:%S
    - **hms**: %H:%M
    - **sql**: SQLite用フォーマット(%Y-%m-%d %H:%M:%S.%f)
    - **ext**: ファイル拡張子用(%Y%m%d-%H%M%S)
    """

    DelimiterStyle: TypeAlias = Literal[
        "slash", "/", "hyphen", "-", "ja", "number", "num", None
    ]
    """区切り記号
    - **slash** | **/**: スラッシュ(ex: %Y/%m/%d)
    - **hyphen** | **-**: ハイフン(ex: %Y-%m-%d)
    - **number** | **num**: 無し (ex: %Y%m%d)
    - **ja**: Japanese Style (ex: %Y%年m%月d日)
    - **None**: 未指定
    """

    def __init__(self, value: AcceptedTypes | None = None):
        """ExtendedDatetimeの初期化

        Args:
            value (`AcceptedTypes` | None, optional): 引数
               - None: 現在時刻(`datetime.now()`)で初期化
        """

        self._dt = self._convert(value) if value else datetime.now()

    def __str__(self) -> str:
        return self.format("sql")

    def __repr__(self) -> str:
        return self.format("sql")

    def __add__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        if isinstance(other, dict):
            delta = relativedelta(**other)
        elif isinstance(other, relativedelta):
            delta = other
        else:
            raise TypeError("Expected dict or relativedelta")

        return ExtendedDatetime(self._dt + delta)

    def __sub__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        if isinstance(other, dict):
            delta = relativedelta(**other)
        elif isinstance(other, relativedelta):
            delta = other
        else:
            raise TypeError("Expected dict or relativedelta")

        return ExtendedDatetime(self._dt - delta)

    def __radd__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        return self.__add__(other)

    def __rsub__(self, other: Union[relativedelta, dict]) -> "ExtendedDatetime":
        return self.__sub__(other)

    def __getattr__(self, name):
        return getattr(self._dt, name)

    @property
    def dt(self) -> datetime:
        """datetime型を返すプロパティ"""
        return self._dt

    def set(self, value: AcceptedTypes) -> None:
        """渡された値をdatetime型に変換して保持

        Args:
            value (str | float | datetime): 入力値
        """

        self._dt = self._convert(value)

    def format(self, fmt: FormatType, delimiter: DelimiterStyle = None) -> str:
        """フォーマット変換

        Args:
            fmt (`FormatType`): 変換形式
            delimiter (`DelimiterStyle`): 区切り

        Raises:
            ValueError: 受け付けない変換形式

        Returns:
            str: 変換文字列
        """

        ret: str
        match fmt:
            case "ts":
                ret = str(self._dt.timestamp())
            case "y":
                match delimiter:
                    case "ja":
                        ret = self._dt.strftime("%Y年")
                    case _:
                        ret = self._dt.strftime("%Y")
            case "ym":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m")
                    case _:
                        ret = self._dt.strftime("%Y/%m")
            case "ymd":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d")
            case "ymdhm":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M")
            case "ymdhms":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S")
                    case "ja":
                        ret = self._dt.strftime("%Y年%m月%d日 %H時%M分%S秒")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M%S")
                    case _:
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S")
            case "sql":
                match delimiter:
                    case "slash" | "/":
                        ret = self._dt.strftime("%Y/%m/%d %H:%M:%S.%f")
                    case "hyphen" | "-":
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
                    case "number" | "num":
                        ret = self._dt.strftime("%Y%m%d%H%M%S%f")
                    case _:
                        ret = self._dt.strftime("%Y-%m-%d %H:%M:%S.%f")
            case "ext":
                ret = self._dt.strftime("%Y%m%d-%H%M%S")
            case _:
                raise ValueError(f"Unknown format: {fmt}")

        return (ret)

    def _convert(self, value: AcceptedTypes) -> datetime:
        """引数の型を判定してdatetimeへ変換

        Args:
            value (`AcceptedTypes`): コンストラクタに与えられた引数

        Raises:
            TypeError: str型が変換できない場合

        Returns:
            datetime: 変換した型
        """

        if isinstance(value, ExtendedDatetime):
            return value.dt
        elif isinstance(value, datetime):
            return value
        elif isinstance(value, float):
            return datetime.fromtimestamp(value)
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%Y/%m/%d %H:%M")
        else:
            raise TypeError("Unsupported type for datetime conversion")
