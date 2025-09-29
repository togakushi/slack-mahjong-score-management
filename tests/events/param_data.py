"""
テスト用パラメータ
"""

from typing import Any, TypedDict

from slack_bolt import App


class FakeBodyDict(TypedDict, total=False):
    """テスト用疑似Body"""
    command: str
    type: str
    event: dict[str, str]


FAKE_CLIENT = App.client

FAKE_BODY: FakeBodyDict = {
    "command": "/mahjong",
    "event": {
        "channel_name": "directmessage",
        "user": "U9999999999",
        "type": "message",
        "ts": "1234567890.123456",
        "thread_ts": "1234567890.123456",
    }
}

message_help: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "麻雀成績ヘルプ"),
    "over ride": ("commandword.ini", "ヘルプの別名"),
    "double word": ("minimal.ini", "麻雀成績ヘルプ 未定義ワード"),
}

message_event: dict[str, tuple[Any, ...]] = {
    # module, config, keyword
    "results: default": ("results", "minimal.ini", "麻雀成績"),
    "results: over ride 1": ("results", "commandword.ini", "麻雀成績の別名１"),
    "results: over ride 2": ("results", "commandword.ini", "麻雀成績の別名２"),
    "results: double word": ("results", "minimal.ini", "麻雀成績 未定義ワード"),

    "graph: default": ("graph", "minimal.ini", "麻雀グラフ"),
    "graph: over ride": ("graph", "commandword.ini", "麻雀グラフの別名"),
    "graph: double word": ("graph", "minimal.ini", "麻雀グラフ 未定義ワード"),

    "ranking: default": ("ranking", "minimal.ini", "麻雀ランキング"),
    "ranking: over ride": ("ranking", "commandword.ini", "麻雀ランキングの別名"),
    "ranking: double word": ("ranking", "minimal.ini", "麻雀ランキング 未定義ワード"),

    "report: default": ("report", "minimal.ini", "麻雀成績レポート"),
    "report: over ride": ("report", "commandword.ini", "麻雀成績レポートの別名"),
    "report: double word": ("report", "minimal.ini", "麻雀成績レポート 未定義ワード"),
}

slash_help: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "help"),
    "double word": ("minimal.ini", "help xxx"),
    "unknown": ("minimal.ini", "xxx"),
}

slash_results: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "results"),
    "alias": ("commandword.ini", "麻雀成績のエイリアス"),
    "double word": ("minimal.ini", "results xxx"),
}

slash_graph: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "graph"),
    "alias": ("commandword.ini", "麻雀グラフのエイリアス"),
    "double word": ("minimal.ini", "graph xxx"),
}

slash_ranking: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "ranking"),
    "alias": ("commandword.ini", "麻雀ランキングのエイリアス"),
    "double word": ("minimal.ini", "ranking xxx"),
}

slash_report: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "report"),
    "alias": ("commandword.ini", "麻雀成績レポートのエイリアス"),
    "double word": ("minimal.ini", "report xxx"),
}

slash_check: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "check"),
    "alias": ("commandword.ini", "チェックのエイリアス"),
    "double word": ("minimal.ini", "check xxx"),
}

slash_download: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "download"),
    "alias": ("commandword.ini", "ダウンロード"),
    "double word": ("minimal.ini", "download xxx"),
}

slash_member_list: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "member"),
    "alias": ("commandword.ini", "メンバー一覧"),
    "double word": ("minimal.ini", "member xxx"),
}

slash_member_add: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "add"),
    "alias 01": ("commandword.ini", "メンバー追加"),
    "alias 02": ("commandword.ini", "入部届"),
    "double word": ("minimal.ini", "add xxx"),
}

slash_member_del: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default 01": ("minimal.ini", "delete"),
    "default 02": ("minimal.ini", "del"),
    "alias 01": ("commandword.ini", "メンバー削除"),
    "alias 02": ("commandword.ini", "退部届"),
    "double word": ("minimal.ini", "del xxx"),
}

slash_team_create: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_create"),
}

slash_team_del: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_del"),
}

slash_team_add: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_add"),
}

slash_team_remove: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_remove"),
}

slash_team_list: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_list"),
}

slash_team_clear: dict[str, tuple[Any, ...]] = {
    # config, keyword
    "default": ("minimal.ini", "team_clear"),
}
