"""
cls/types.py
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeAlias, TypedDict, Union

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd


class TeamDataDict(TypedDict):
    """チーム情報格納辞書"""

    id: int
    team: str
    member: list[str]


MessageType: TypeAlias = Union[None, str, "Path", "pd.DataFrame"]
"""メッセージ型
- *None*: 空データ(なにもしない)
- *str*: 文字列型データ(そのまま表示)
- *Path*: ファイルパス(アップロード処理)
- *DataFrame*: 表データ
"""


@dataclass
class StyleOptions:
    """表示オプション"""

    codeblock: bool = False
    """MessageTypeがstr型ならcodeblock化
    - *True*: codeblock化
    - *False*: 何もしない
    """
    show_index: bool = False
    """MessageTypeがDataFrame型なら表にIndexに含める
    - *True*: Indexを含める
    - *False*: Indexを含めない
    """
    use_comment: bool = False
    """ファイルアップロード時のinitial_commentを有効にする
    - *True*: initial_commentを使う
    - *False*: initial_commentを使わない
    """
    header_hidden: bool = False
    """ヘッダ文を非表示にする
    - *True*: 非表示
    - *False*: 表示
    """
    key_title: bool = True
    """小見出しに辞書のキーを使う
    - *True*: 表示
    - *False*: 非表示
    """
    summarize: bool = True
    """MessageTypeがstr型のとき後続の要素を集約する
    - *True*: 可能な限り複数の要素をひとつにまとめる
    - *False*: 要素単位でデータを処理する
    """


class MessageTypeDict(TypedDict):
    """メッセージ格納辞書"""

    data: MessageType
    """内容"""
    options: StyleOptions
    """表示オプション"""


class RemarkDict(TypedDict):
    """メモ格納用辞書"""

    thread_ts: str
    """ゲーム終了時間"""
    event_ts: str
    """メモ記録時間"""
    name: str
    matter: str


class RankTableDict(TypedDict):
    """昇段ポイント計算テーブル用辞書"""

    grade: str
    """段位名称"""
    point: list
    """初期ポイントと昇段に必要なポイント"""
    acquisition: list
    """獲得ポイント(順位)"""
    demote: bool
    """降格フラグ
    - *True*: 降格する(省略時デフォルト)
    - *False*: 降格しない
    """


class GradeTableDict(TypedDict, total=False):
    """段位テーブル用辞書"""

    name: str
    """識別名"""
    addition_expression: str
    """素点評価式(昇段ポイントに加算)"""
    table: list[RankTableDict]
    """昇段ポイント計算テーブル"""
