# セットアップ手順

## アプリの作成

Slack api のWebページから登録を行う。

https://api.slack.com/apps

[Create New App] -> From scratch

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
    - message.groups ※プライベートチャンネルで利用する場合のみ
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
詳細は[権限リスト](permission.md)を参照。

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

## 実行環境構築

> [!CAUTION]
> Python3.12以上の実行環境が必要

* [uv を使って環境構築する場合](using_uv.md)
* [venv を使って環境構築する場合](using_venv.md)

## 初期設定

### チャンネルにアプリを登録
Integrations -> Add apps<br />
忘れがち。

### メンバーの登録
スラッシュコマンドで追加。
