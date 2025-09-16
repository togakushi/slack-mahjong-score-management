"""
integrations/slack/config.py
"""

from dataclasses import dataclass, field

from integrations.base.interface import IntegrationsConfig


@dataclass
class AppConfig(IntegrationsConfig):
    """設定値"""

    slash_command: str = field(default="/mahjong")
    """スラッシュコマンド名"""

    comparison_word: str = field(default="成績チェック")
    """データ突合コマンド呼び出しキーワード"""
    comparison_alias: str = field(default="")
    """データ突合スラッシュコマンド別名(カンマ区切り)"""

    search_channel: str = field(default="")
    """テータ突合時に成績記録ワードを検索するチャンネル名"""
    search_after: int = field(default=7)
    """データ突合時対象にする日数"""
    search_wait: int = field(default=180)
    """指定秒数以内にポストされているデータは突合対象から除外する"""

    thread_report: bool = field(default=True)
    """スレッド内にある得点報告を扱う"""

    # リアクション文字列
    reaction_ok: str = field(default="ok")
    """DBに取り込んだ時に付けるリアクション"""
    reaction_ng: str = field(default="ng")
    """DBに取り込んだが正確な値ではない可能性があるときに付けるリアクション"""

    # 制限
    ignore_userid: list = field(default_factory=list)
    """投稿を無視するユーザのリスト(カンマ区切りで設定)"""
    channel_limitations: list = field(default_factory=list)
    """SQLを実行できるチャンネルリスト"""

    # 装飾オプション
    badge_degree: bool = field(default=False)
    """プレイしたゲーム数に対して表示される称号"""
    badge_status: bool = field(default=False)
    """勝率に対して付く調子バッジ"""
