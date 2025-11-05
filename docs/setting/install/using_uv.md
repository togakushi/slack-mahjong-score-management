# uvを使った実行環境構築

## uvインストール

公式ドキュメントを参照

* https://docs.astral.sh/uv/getting-started/installation/

## 本体インストール
```
$ git clone https://github.com/togakushi/slack-mahjong-score-management.git
```

## グラフ描写用の日本語フォント
IPAexフォント（ipaexg.ttf）を `app.py` と同じディレクトリに配置

* https://moji.or.jp/ipafont/ipafontdownload/

## 環境変数
発行されたトークンを環境変数にセット

* Slack利用時
  ```
  $ export SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  $ export SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  $ export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
  ```
* Discord利用時
  ```
  $ export DISCORD_TOKEN=XXXXXXXXXXXXXXXXXXXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

## 起動
### 通常起動
```
$ uv run app.py
```

### 環境変数をファイルに記述する場合
`app.env` などの任意のファイル名で環境変数を記述したファイルを準備する
* 記述例
  ```
  $ cat app.env
  SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
  ```
* 起動
  ```
  $ uv run --env-file=app.env app.py
  ```

### バックグラウンド起動
```
$ nohup uv run app.py > /dev/null 2>&1 &
```

#### 停止
PIDを調べてプロセスをkill。

## 備考
uv実行時に自動で以下が行われる
* Python3.12のインストール(利用していなければ)
* 仮想環境の作成
* 依存パッケージのインストール
* スクリプトの起動
