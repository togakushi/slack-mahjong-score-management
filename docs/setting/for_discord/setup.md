# セットアップ手順
## アプリケーションの作成
1. https://discord.com/developers/applications にアクセス
2. [Applications] > [New Application] を選択
3. [Create an application] の [Name] にBotの名前を入力
4. 利用規約にチェックを入れ [Create] をクリック

## アプリケーションの設定
[My applications] で設定を行う。

### トークンの発行
[Bot] > [Token] > [Reset Token]

発行されたトークンは環境変数 `DISCORD_TOKEN` にセットして利用する。

### 認証
[OAuth2] > [OAuth2 URL Generator] > [Scopes] の [bot] にチェックを入れる

[Bot Permissions] で以下を選択
- Text Permissions
  - Send Message
  - Create Public Threads
  - Attach Files
  - Read Message History
  - Add Reactions
  - Use Slash Commands

[Generated URL] に表示されている URL にアクセスし、Botをサーバーに参加させる

### Intents 許可
[bot] > [Privileged Gateway Intents]
- Presence Intent [OFF]
- Server Members Intent [OFF]
- Message Content Intent [ON] **必須**


### メンバーの登録
スラッシュコマンドで追加。
