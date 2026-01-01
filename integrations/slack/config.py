"""
integrations/slack/config.py
"""

from dataclasses import dataclass, field

from integrations.base.interface import IntegrationsConfig
from integrations.slack.events import comparison, slash


@dataclass
class SvcConfig(IntegrationsConfig):
    """slack用個別設定値"""

    slash_command: str = field(default="/mahjong")
    """スラッシュコマンド名"""

    comparison_word: str = field(default="成績チェック")
    """データ突合コマンド呼び出しキーワード"""
    comparison_alias: list = field(default_factory=list)
    """データ突合スラッシュコマンド別名(カンマ区切りで設定)"""

    search_channel: list = field(default_factory=list)
    """テータ突合時に成績記録ワードを検索するチャンネル名(カンマ区切りで設定)"""
    search_after: int = field(default=7)
    """データ突合時対象にする日数"""
    search_wait: int = field(default=180)
    """指定秒数以内にポストされているデータを突合対象から除外する"""

    thread_report: bool = field(default=True)
    """スレッド内にある得点報告の扱い

    - *True*: スレッド内の点数報告も取り込む
    - *False*: スレッド内の点数報告は無視する
    """

    # リアクション文字列
    reaction_ok: str = field(default="ok")
    """DBに取り込んだ時に付けるリアクション"""
    reaction_ng: str = field(default="ng")
    """DBに取り込んだが正確な値ではない可能性があるときに付けるリアクション"""

    # 制限
    ignore_userid: list = field(default_factory=list)
    """投稿を無視するユーザのリスト(カンマ区切りで設定)"""
    channel_limitations: list = field(default_factory=list)
    """SQLが実行できるチャンネルリスト(カンマ区切りで設定)

    未定義はすべてのチャンネルでSQLが実行できる
    """

    bot_id: str = field(default="")
    """ボットID"""

    tab_var: dict = field(default_factory=dict)
    """ホームタブ用初期値"""

    def __post_init__(self):
        self.read_file("slack")

        # スラッシュコマンドはスラッシュ始まり
        if not self.slash_command.startswith("/"):
            self.slash_command = f"/{self.slash_command}"

        # スラッシュコマンド登録
        self._command_dispatcher.update({"help": slash.command_help})
        self._command_dispatcher.update({"check": comparison.main})
        for alias in self.comparison_alias:
            self._command_dispatcher.update({alias: comparison.main})

        # 個別コマンド登録
        self._keyword_dispatcher.update(
            {
                self.comparison_word: comparison.main,
                f"Reminder: {self.comparison_word}": comparison.main,
            }
        )
