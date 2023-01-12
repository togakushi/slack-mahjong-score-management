# セットアップ手順

## slack

### アプリの作成

https://api.slack.com/

[Create an app] -> From scratch

- App Name (任意)
- Pick a workspace to develop your app in: (ワークスペース選択)

### ソケットモード有効化

Settings -> Socket Mode

- Enable Socket Mode (有効化)
- Token Name (任意)
- [Generate]

`App-Level Tokens` が発行される。

### スラッシュコマンド有効化

Features -> Slash Commands

- [Create New Command]
  - Command (config.iniと合わせる)
  - Short Description  (任意)
  - [Save]

### イベント設定

Features -> Event Subscriptions

- Enable Events (On)
- Subscribe to bot events
  - [Add Bot User Event]
    - message.channels
    - [Save Changes]

追加する。

### 権限設定

Features -> OAuth & Permissions

- Bot Token Scopes
  - commands
  - channels:history
  - chat:write
  - chat:write.customize
  - files:write

追加する。

- User Token Scopes
  - channels:history

追加する。トークン発行後は不要なので削除可。

### アプリ設定

Features -> App Home

- App Display Name [Edit]
  - Display Name (Bot Name)
  - Default username (任意)
  - [add]

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
$ python3 -m venv venv-mahjong-score-management
$ source ./venv-mahjong-score-management/bin/activate
```

### 依存パッケージのインストール

```
(venv-mahjong-score-management) $ cd slack-mahjong-score-management
(venv-mahjong-score-management) $ pip install -U pip
(venv-mahjong-score-management) $ pip install -r requirements.txt
```

### グラフ描写用の日本語フォント
IPAexフォント（ipaexg.tt）を `slack-app.py` と同じディレクトリに配置

https://moji.or.jp/ipafont/ipafontdownload/


### 起動
発行されたトークンを環境変数にセット
```
(venv-mahjong-score-management) $ export SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venv-mahjong-score-management) $ export SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venv-mahjong-score-management) $ export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```
動かしっぱなしにする
```
(venv-mahjong-score-management) $ nohup python3 slack-app.py -c config.ini > /dev/null 2>&1 &
```

### 停止
PIDを調べてプロセスをkill。

## 初期設定

### チャンネルにアプリを登録
Integrations -> Add apps

### メンバーの登録
スラッシュコマンドで追加。
saveを忘れずに。

### アーカイブ機能を使う場合はDBの初期化
後で書く。
