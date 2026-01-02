# 最小構成
## メイン設定
必須セクションだけ設定し、すべてデフォルト値の状態。
```
[mahjong]

[setting]

```

### 設定状況(アプリケーション起動ログから抜粋)
#### 使用データベースファイル
```
[DEBUG][initialization:initialization_resultdb] /path/to/slack-mahjong-score-management/mahjong.db
```

#### 呼び出しキーワード
```
[DEBUG][configuration:register] keyword_dispatcher:
        麻雀成績ヘルプ: <function register.<locals>.dispatch_help at 0x7eff017dd3a0>
        麻雀成績: <function main at 0x7efefdcc7560>
        麻雀グラフ: <function main at 0x7efefe0eaca0>
        麻雀ランキング: <function main at 0x7efefe115080>
        麻雀成績レポート: <function main at 0x7efefdcc6520>
        メンバー一覧: <function register.<locals>.dispatch_members_list at 0x7efefca4aa20>
        チーム一覧: <function register.<locals>.dispatch_team_list at 0x7efefca4ab60>
```
Slack/Discordを利用時は突合コマンドが追加される
```
        成績チェック: <function main at 0x7fd52656a3e0>
        Reminder: 成績チェック: <function main at 0x7fd52656a3e0>
```

#### スラッシュコマンド
```
[DEBUG][configuration:register] command_dispatcher:
        results: <function main at 0x7efefdcc7560>
        成績: <function main at 0x7efefdcc7560>
        graph: <function main at 0x7efefe0eaca0>
        グラフ: <function main at 0x7efefe0eaca0>
        ranking: <function main at 0x7efefe115080>
        ランキング: <function main at 0x7efefe115080>
        report: <function main at 0x7efefdcc6520>
        レポート: <function main at 0x7efefdcc6520>
        member: <function register.<locals>.dispatch_members_list at 0x7efefca4aa20>
        userlist: <function register.<locals>.dispatch_members_list at 0x7efefca4aa20>
        member_list: <function register.<locals>.dispatch_members_list at 0x7efefca4aa20>
        team_list: <function register.<locals>.dispatch_team_list at 0x7efefca4ab60>
        download: <function register.<locals>.dispatch_download at 0x7efefca4a980>
        ダウンロード: <function register.<locals>.dispatch_download at 0x7efefca4a980>
        add: <function register.<locals>.dispatch_member_append at 0x7efefca4aac0>
        del: <function register.<locals>.dispatch_member_remove at 0x7efefca4ac00>
        team_create: <function register.<locals>.dispatch_team_create at 0x7efefca4aca0>
        team_del: <function register.<locals>.dispatch_team_delete at 0x7efefca4ad40>
        team_add: <function register.<locals>.dispatch_team_append at 0x7efefca4ade0>
        team_remove: <function register.<locals>.dispatch_team_remove at 0x7efefca4ae80>
        team_clear: <function register.<locals>.dispatch_team_clear at 0x7efefca4af20>
```
Slack/Discordを利用時は突合コマンドが追加される
```
        check: <function main at 0x7fd52656a3e0>
```

### 各セクション設定状況
```
[DEBUG][config:config_load] setting: {'help': '麻雀成績ヘルプ', 'keyword': '終局', 'remarks_word': '麻雀成績メモ', 'rule_config': PosixPath('files/default_rule.ini'), 'time_adjust': 12, 'separate': False, 'search_word': '', 'group_length': 0, 'guest_mark': '※', 'database_file': PosixPath('mahjong.db'), 'backup_dir': None, 'font_file': PosixPath('/path/to/slack-mahjong-score-management/ipaexg.ttf'), 'graph_style': 'ggplot', 'work_dir': PosixPath('work'), 'section': 'setting'}
[DEBUG][config:config_load] mahjong: {'mode': 4, 'rule_version': 'default_rule', 'origin_point': 250, 'return_point': 300, 'rank_point': [30, 10, -10, 30], 'ignore_flying': False, 'draw_split': False, 'section': 'mahjong'}
[DEBUG][config:config_load] alias: {'results': ['results', '成績'], 'graph': ['graph', 'グラフ'], 'ranking': ['ranking', 'ランキング'], 'report': ['report', 'レポート'], 'download': ['download', 'ダウンロード'], 'member': ['member', 'userlist', 'member_list'], 'add': ['add'], 'delete': ['del', 'del'], 'team_create': ['team_create'], 'team_del': ['team_del'], 'team_add': ['team_add'], 'team_remove': ['team_remove'], 'team_list': ['team_list'], 'team_clear': ['team_clear'], 'section': 'alias'}
[DEBUG][config:config_load] member: {'info': [], 'registration_limit': 255, 'character_limit': 8, 'alias_limit': 16, 'guest_name': 'ゲスト', 'section': 'member', 'commandword': ['メンバー一覧']}
[DEBUG][config:config_load] team: {'info': [], 'registration_limit': 255, 'character_limit': 16, 'member_limit': 16, 'friendly_fire': True, 'section': 'team', 'commandword': ['チーム一覧']}
[DEBUG][config:config_load] results: {'section': 'results', 'commandword': ['麻雀成績'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] graph: {'section': 'graph', 'commandword': ['麻雀グラフ'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] ranking: {'section': 'ranking', 'commandword': ['麻雀ランキング'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
[DEBUG][config:config_load] report: {'section': 'report', 'commandword': ['麻雀成績レポート'], 'aggregation_range': '当日', 'individual': True, 'all_player': False, 'daily': True, 'fourfold': True, 'game_results': False, 'guest_skip': True, 'guest_skip2': True, 'ranked': 3, 'score_comparisons': False, 'statistics': False, 'stipulated': 0, 'stipulated_rate': 0.05, 'unregistered_replace': True, 'anonymous': False, 'verbose': False, 'versus_matrix': False, 'collection': '', 'always_argument': [], 'target_mode': 0, 'format': '', 'filename': '', 'interval': 80}
```

### サービス個別設定状況
> [!CAUTION]
> `slash_command`の不一致に注意！！

#### Slack
```
[DEBUG][interface:read_file] slack: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7fb5cdadb8c0>, slash_command='/mahjong', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='matplotlib', comparison_word='成績チェック', comparison_alias=[], search_channel=[], search_after=7, search_wait=180, thread_report=True, reaction_ok='ok', reaction_ng='ng', ignore_userid=[], channel_limitations=[], bot_id='', tab_var={})
```

#### Discord
```
[DEBUG][interface:read_file] discord: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7f2ce3be78c0>, slash_command='mahjong', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='matplotlib', comparison_word='成績チェック', comparison_alias=[], search_after=7, ignore_userid=[], channel_limitations=[], bot_name=None)
```

#### Web
```
[DEBUG][interface:read_file] web: SvcConfig(_command_dispatcher={}, _keyword_dispatcher={}, config_file=<configparser.ConfigParser object at 0x7f2b8a1f78c0>, slash_command='', badge_degree=False, badge_status=False, badge_grade=False, plotting_backend='plotly', host='', port=0, require_auth=False, username='', password='', use_ssl=False, certificate='', private_key='', view_summary=True, view_graph=True, view_ranking=True, view_report=True, management_member=False, management_score=False, theme='', custom_css='')
```

## ルールセット設定
省略されているため[*default_rule.ini*](../../../files/default_rule.ini)が読み込まれる。

### ルールセット登録状況
```
[INFO][rule:info] keyword_mapping: {'終局': 'default_rule'}
[INFO][rule:info] default_rule: mode=4, origin_point=250, return_point=300, rank_point=[30, 10, -10, -30], draw_split=False, ignore_flying=False
[INFO][rule:info] default_rule3: mode=3, origin_point=350, return_point=400, rank_point=[30, 0, -30], draw_split=False, ignore_flying=False
```
