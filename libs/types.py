"""
cls/types.py
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeAlias, TypedDict, Union

if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd

    from cls.timekit import ExtendedDatetime


@dataclass
class Args:
    """コマンドラインオプション"""

    service: str
    config: "Path"
    """設定ファイルパス"""

    debug: int
    """デバッグ出力フラグ"""
    verbose: int
    """詳細出力フラグ"""

    moderate: bool
    """INFO以下のログレベル出力を抑止"""
    notime: bool
    """ログに日付を付与しない"""

    # Only allowed when --service=standard_io
    text: str

    # Only allowed when --service=web
    host: str
    port: int

    # dbtools
    compar: bool
    unification: "Path"
    recalculation: bool
    export_data: str
    import_data: str
    vacuum: bool
    gen_test_data: int
    testcase: Optional["Path"]


class MemberDataDict(TypedDict):
    """メンバー情報格納辞書"""

    id: int
    """メンバーID"""

    name: str
    """メンバー名"""

    alias: list[str]
    """別名リスト"""


class TeamDataDict(TypedDict):
    """チーム情報格納辞書"""

    id: int
    """チームID"""
    team: str
    """チーム名"""
    member: list[str]
    """所属メンバーリスト"""


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

    format_type: Literal["default", "csv", "txt"] = "default"
    """出力フォーマット"""

    base_name: str = ""
    """ファイル出力時のファイル名"""

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
    indent: int = 0
    """インデント数(TAB)"""
    keep_blank: bool = False
    """空行の削除
    - *True*: 削除しない
    - *False*: 削除する
    """

    @property
    def filename(self) -> str:
        """出力ファイル名"""
        if self.format_type == "default":
            return ""
        return f"{self.base_name}.{self.format_type}"


class PlaceholderDict(TypedDict, total=False):
    """プレースホルダ用パラメータ"""

    command: str
    """コマンド名"""

    # プレイヤー関連
    player_name: str
    """集計対象プレイヤー"""
    guest_name: str
    """ゲストの名前"""
    target_player: list[str]
    """比較対象プレイヤーリスト"""
    player_list: dict[str, str]
    """集計対象プレイヤーリスト"""
    competition_list: dict[str, str]
    """比較対象プレイヤーリスト"""
    all_player: bool
    """集計範囲内の登録済みプレイヤーを対象にする"""
    anonymous: bool
    """プレイヤー名の匿名化"""
    unregistered_replace: bool
    """未登録プレイヤー名置換フラグ
    - *True*: 置換する
    - *False*: 置換しない
    """

    # 集計関連
    individual: bool
    """個人集計フラグ
    - *True*: 個人戦集計
    - *False*: チーム戦集計
    """
    guest_skip: bool
    """ゲストを集計対象に含めるか
    - *True*: 集計結果にゲストを含める
    - *False*: 集計結果からゲストを除外する
    """
    guest_skip2: bool
    friendly_fire: bool
    """チーム戦集計時のチーム同卓ゲームの扱い
    - *True*: チーム同卓ゲームを集計(同じチームのポイントは合算される)
    - *False*: チーム同卓ゲームを集計対象外にする
    """
    collection: Literal["daily", "monthly", "yearly", "all"]
    """集約範囲"""

    ranked: int
    """ランキングに含める順位"""
    stipulated: int
    """集計規定ゲーム数"""
    interval: int
    """区間集計範囲"""
    target_count: int
    """直近ゲーム数指定"""
    source: str
    """スコア入力元識別子"""
    separate: bool
    """スコア入力元識別子別集計フラグ
    - *True*: 識別子別に集計
    - *False*: すべて集計
    """

    # 検索関連
    starttime: Union[str, "ExtendedDatetime", None]
    """集計開始日時"""
    endtime: Union[str, "ExtendedDatetime", None]
    """集計終了日時"""
    onday: Union[str, "ExtendedDatetime", None]
    """time_adjust修正を含まない日時"""

    search_word: str
    """コメント検索文字列"""
    group_length: int
    """コメント検索時に指定文字数でグループ化する"""

    # 出力関連
    format: Literal["default", "csv", "txt"]
    """出力フォーマット指定"""
    filename: str
    """出力ファイル名"""

    # 表示モード切替フラグ
    score_comparisons: bool
    """スコア比較モード"""
    game_results: bool
    """"""
    order: bool
    """順位表示モード"""
    versus_matrix: bool
    """対戦結果表示モード"""
    statistics: bool
    """統計表示モード"""
    rating: bool
    """レーティング表示モード"""
    verbose: bool
    """詳細表示モード"""
    fourfold: bool
    """内部フラグ(縦持ちデータで集計)"""

    # ルール情報
    mode: int
    """集計モード"""
    target_mode: int
    """集計モード(オプション指定)"""
    default_rule: str
    """ルール識別子(設定値)"""
    rule_version: str
    """ルール識別子(指定値)"""
    rule_set: dict[str, dict[str, Any]]
    """集計対象ルール識別子"""
    mixed: bool
    """ルール識別子の扱い
    - *True*: 定義済みすべてのルール識別子を含める
    - *False*: ルール識別子を個別指定
    """
    origin_point: int
    """配給原点"""
    return_point: int
    """返し点"""

    # その他
    undefined_word: int
    """未登録ワードの扱い
    - *0*: 役満扱い
    - *1*: 卓外清算(個人清算)
    - *2*: カウントのみ
    - *3*: 卓外清算(チーム清算)
    """


class MessageTypeDict(TypedDict):
    """メッセージ格納辞書"""

    data: MessageType
    """内容"""
    options: StyleOptions
    """表示オプション"""


class ScoreDict(TypedDict, total=False):
    """スコアデータ格納用辞書"""

    ts: str
    """ゲーム終了時間"""

    p1_name: str
    """東家：プレイヤー名"""
    p1_str: str
    """東家：入力された素点情報(文字列)"""
    p1_rpoint: int
    """東家：素点(入力文字列評価後)"""
    p1_point: float
    """東家：獲得ポイント"""
    p1_rank: int
    """東家：獲得順位"""

    p2_name: str
    """南家：プレイヤー名"""
    p2_str: str
    """南家：入力された素点情報(文字列)"""
    p2_rpoint: int
    """南家：素点(入力文字列評価後)"""
    p2_point: float
    """東家：獲得ポイント"""
    p2_rank: int
    """南家：獲得順位"""

    p3_name: str
    """西家：プレイヤー名"""
    p3_str: str
    """西家：入力された素点情報(文字列)"""
    p3_rpoint: int
    """西家：素点(入力文字列評価後)"""
    p3_point: float
    """西家：獲得ポイント"""
    p3_rank: int
    """西家：獲得順位"""

    p4_name: str
    """北家：プレイヤー名"""
    p4_str: str
    """北家：入力された素点情報(文字列)"""
    p4_rpoint: int
    """北家：素点(入力文字列評価後)"""
    p4_point: float
    """北家：獲得ポイント"""
    p4_rank: int
    """北家：獲得順位"""

    deposit: int
    """配給原点合計 - 素点合計"""
    comment: Optional[str]
    """ゲームコメント"""
    rule_version: str
    """ルール識別子"""
    source: Optional[str]
    """データ入力元識別子"""
    mode: Literal[3, 4]
    """集計モード"""


class RemarkDict(TypedDict, total=False):
    """メモ格納用辞書"""

    thread_ts: str
    """ゲーム終了時間"""
    event_ts: str
    """メモ記録時間"""
    name: str
    """記録対象プレイヤー名"""
    matter: str
    """記録内容"""
    source: str
    """データ入力元識別子"""


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
