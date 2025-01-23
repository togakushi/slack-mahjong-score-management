# セットアップ手順

## slack

### アプリの作成

https://api.slack.com/

[Create an app] -> From scratch

- App Name (任意)
- Pick a workspace to develop your app in: (ワークスペース選択)

### ソケットモード有効化

Settings -> Socket Mode

- Enable Socket Mode (有効)
- Token Name (任意)
- [Generate]

`App-Level Tokens` が発行される。

### スラッシュコマンド有効化

Features -> Slash Commands

- [Create New Command]
  - Command (任意)
    - config.iniと合わせる
    - 既存のコマンドと被らないように
  - Short Description (任意)
- [Save]

### イベント設定

Features -> Event Subscriptions

- Enable Events (On)
- Subscribe to bot events
  - [Add Bot User Event]
    - app_home_opened ※Home Appを利用する場合のみ
    - message.channels
    - message.im ※DMから機能呼び出しキーワードを利用する場合のみ
  - [Save Changes]

必要な権限を追加する。

### 権限設定

Features -> OAuth & Permissions

- Bot Token Scopes
  - chat:write
  - files:write
  - im:write
  - reactions:read
  - reactions:write

足りないものは追加する。

- User Token Scopes
  - search:read

追加する。<br>
詳細は[権限リスト](../api_list.md)を参照。

### アプリ設定

Features -> App Home

- App Display Name [Edit]
  - Display Name (Bot Name)
  - Default username (任意)
  - [add]
- Show Tabs
  - Home Tab (有効) ※Home Appを使うときのみ
  - Messages Tab (有効)
    - Allow users to send Slash commands and messages from the messages tab (チェック)

### インストール

Settings -> Install App

- [Install to Workspace]
- [Allow]

`User OAuth Token` と `Bot User OAuth Token` が発行される

## 実行環境

### 本体インストール

```
$ git clone https://github.com/togakushi/slack-mahjong-score-management.git
```

### 仮想環境の作成

作成するディレクトリ名は任意。

```
$ python3 -m venv venvdir
$ source ./venvdir/bin/activate
```

### 依存パッケージのインストール

```
(venvdir) $ cd slack-mahjong-score-management
(venvdir) $ pip install -U pip
(venvdir) $ pip install -r requirements.txt
```

### グラフ描写用の日本語フォント
IPAexフォント（ipaexg.ttf）を `slack-app.py` と同じディレクトリに配置

https://moji.or.jp/ipafont/ipafontdownload/


### 起動
発行されたトークンを環境変数にセット
```
(venvdir) $ export SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venvdir) $ export SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venvdir) $ export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```
動かしっぱなしにする
```
(venvdir) $ nohup python3 slack-app.py -c config.ini > /dev/null 2>&1 &
```

### 停止
PIDを調べてプロセスをkill。

## 初期設定

### チャンネルにアプリを登録
Integrations -> Add apps<br />
忘れがち。

### メンバーの登録
スラッシュコマンドで追加。
