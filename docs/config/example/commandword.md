# 呼び出しコマンド定義
## メイン設定
コマンド名の設定を行う。
```
[mahjong]

[setting]
keyword = 成績記録
remarks_word = ゲーム内メモ
help = アプリヘルプ

[alias] # 一部のみ指定
download = ダウンロード
member = userlist, メンバー, リスト
add = 追加, 入部届
del = 削除, 退部届

[results]
commandword = 成績サマリ, 成績サマリ2

[graph]
commandword = 成績グラフ, 成績グラフ2

[ranking]
commandword = 成績ランキング

[report]
commandword = 成績レポート

[member]
commandword = 部員リスト

[team]
commandword = チーム一覧, チーム構成

[slack]
comparison_word = 成績突合
comparison_alias = 突合

[discord]
comparison_word = 成績突合
comparison_alias = 突合
```

### 設定状況(アプリケーション起動ログから抜粋)
#### 使用データベースファイル
```
[DEBUG][initialization:initialization_resultdb] /path/to/slack-mahjong-score-management/mahjong.db
```

#### 呼び出しキーワード
```
[DEBUG][configuration:register] keyword_dispatcher:
        アプリヘルプ: <function register.<locals>.dispatch_help at 0x7feccc4093a0>
        成績サマリ: <function main at 0x7fecc8907560>
        成績サマリ2: <function main at 0x7fecc8907560>
        成績グラフ: <function main at 0x7fecc8d2aca0>
        成績グラフ2: <function main at 0x7fecc8d2aca0>
        成績ランキング: <function main at 0x7fecc8d55080>
        成績レポート: <function main at 0x7fecc8906520>
        部員リスト: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        チーム一覧: <function register.<locals>.dispatch_team_list at 0x7fecc76ed260>
        チーム構成: <function register.<locals>.dispatch_team_list at 0x7fecc76ed260>
```
Slack/Discordを利用時は突合コマンドが追加される
```
        成績突合: <function main at 0x7fecc7a423e0>
        Reminder: 成績突合: <function main at 0x7fecc7a423e0>
```

#### スラッシュコマンド
```
[DEBUG][configuration:register] command_dispatcher:
        results: <function main at 0x7fecc8907560>
        成績: <function main at 0x7fecc8907560>
        graph: <function main at 0x7fecc8d2aca0>
        グラフ: <function main at 0x7fecc8d2aca0>
        ranking: <function main at 0x7fecc8d55080>
        ランキング: <function main at 0x7fecc8d55080>
        report: <function main at 0x7fecc8906520>
        レポート: <function main at 0x7fecc8906520>
        member: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        userlist: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        member_list: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        メンバー: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        リスト: <function register.<locals>.dispatch_members_list at 0x7fecc7672c00>
        team_list: <function register.<locals>.dispatch_team_list at 0x7fecc76ed260>
        download: <function register.<locals>.dispatch_download at 0x7fecc7a65760>
        ダウンロード: <function register.<locals>.dispatch_download at 0x7fecc7a65760>
        add: <function register.<locals>.dispatch_member_append at 0x7fecc75dad40>
        追加: <function register.<locals>.dispatch_member_append at 0x7fecc75dad40>
        入部届: <function register.<locals>.dispatch_member_append at 0x7fecc75dad40>
        del: <function register.<locals>.dispatch_member_remove at 0x7fecc75dade0>
        削除: <function register.<locals>.dispatch_member_remove at 0x7fecc75dade0>
        退部届: <function register.<locals>.dispatch_member_remove at 0x7fecc75dade0>
        team_create: <function register.<locals>.dispatch_team_create at 0x7fecc75db060>
        team_del: <function register.<locals>.dispatch_team_delete at 0x7fecc75db100>
        team_add: <function register.<locals>.dispatch_team_append at 0x7fecc75db9c0>
        team_remove: <function register.<locals>.dispatch_team_remove at 0x7fecc75dba60>
        team_clear: <function register.<locals>.dispatch_team_clear at 0x7fecc75dbb00>
        help: <function command_help at 0x7fecc7a42980>
```
Slack/Discordを利用時は突合コマンドが追加される
```
        check: <function main at 0x7fecc7a423e0>
        突合: <function main at 0x7fecc7a423e0>
```

### 各セクション設定状況
```
[DEBUG][config:config_load] setting: {'help': 'アプリヘルプ', 'keyword': '成績記録', 'remarks_word': 'ゲーム内メモ', 'rule_config': PosixPath('files/default_rule.ini'), 'time_adjust': 12, 'separate': False, 'search_word': '', 'group_length': 0, 'guest_mark': '※', 'database_file': PosixPath('mahjong.db'), 'backup_dir': None, 'font_file': PosixPath('/path/to/slack-mahjong-score-management/ipaexg.ttf'), 'graph_style': 'ggplot', 'work_dir': PosixPath('work'), 'section': 'setting'}
[DEBUG][config:config_load] mahjong: {'mode': 4, 'rule_version': 'default_rule', 'origin_point': 250, 'return_point': 300, 'rank_point': [30, 10, -10, 30], 'ignore_flying': False, 'draw_split': False, 'section': 'mahjong'}
[DEBUG][config:config_load] alias: {'results': ['results', '成績'], 'graph': ['graph', 'グラフ'], 'ranking': ['ranking', 'ランキング'], 'report': ['report', 'レポート'], 'download': ['download', 'ダウンロード', 'ダウンロード'], 'member': ['member', 'userlist', 'member_list', 'userlist', 'メンバー', 'リスト'], 'add': ['add', '追加', '入部届'], 'delete': ['del', '削除', '退部届'], 'team_create': ['team_create'], 'team_del': ['team_del'], 'team_add': ['team_add'], 'team_remove': ['team_remove'], 'team_list': ['team_list'], 'team_clear': ['team_clear'], 'del': None, 'section': 'alias'}
[DEBUG][config:config_load] member: {'info': [], 'registration_limit': 255, 'character_limit': 8, 'alias_limit': 16, 'guest_name': 'ゲスト', 'commandword': ['部員リスト'], 'section': 'member'}
[DEBUG][config:config_load] team: {'info': [], 'registration_limit': 255, 'character_limit': 16, 'member_limit': 16, 'friendly_fire': True, 'commandword': ['チーム一覧', 'チーム構成'], 'section': 'team'}
[DEBUG][config:config_load] results: {'section': 'results', 'commandword': ['成績サマリ', '成績サマリ2'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] graph: {'section': 'graph', 'commandword': ['成績グラフ', '成績グラフ2'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] ranking: {'section': 'ranking', 'commandword': ['成績ランキング'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] report: {'section': 'report', 'commandword': ['成績レポート'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
```

### サービス個別設定状況
> [!CAUTION]
> `slash_command`の不一致に注意！！

#### Slack
```
[DEBUG][interface:read_file] slack: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7fecc77378c0>, slash_command='/mahjong', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='matplotlib', comparison_word='成績突合', comparison_alias=['突合'], search_channel=[], search_after=7, search_wait=180, thread_report=True, reaction_ok='ok', reaction_ng='ng', ignore_userid=[], channel_limitations=[], bot_id='', tab_var={})
```

#### Discord
```
[DEBUG][interface:read_file] discord: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7fb1ec5278c0>, slash_command='mahjong', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='matplotlib', comparison_word='成績突合', comparison_alias=['突合'], search_after=7, ignore_userid=[], channel_limitations=[], bot_name=None)
```

#### Web
```
[DEBUG][interface:read_file] web: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7f19641c38c0>, slash_command='', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='plotly', host='', port=0, require_auth=False, username='', password='', use_ssl=False, certificate='', private_key='', view_summary=True, view_graph=True, view_ranking=True, view_report=True, management_member=False, management_score=False, theme='', custom_css='')
```

## ルールセット設定
省略されているため[*default_rule.ini*](../../../files/default_rule.ini)が読み込まれる。

### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'成績記録': 'default_rule'}
[INFO][rule:info] default_rule: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, 30], draw_split=False, ignore_flying=False
[INFO][rule:info] default_rule3: mode=3, origin_point=350, return_point=400, rank_point=[30, 0, -30], draw_split=False, ignore_flying=False
```
