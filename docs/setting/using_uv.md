# uvを使った実行環境構築

## uvインストール

公式ドキュメントを参照

* https://docs.astral.sh/uv/getting-started/installation/

## 本体インストール
```
$ git clone https://github.com/togakushi/slack-mahjong-score-management.git
```

## グラフ描写用の日本語フォント
IPAexフォント（ipaexg.ttf）を `slack-app.py` と同じディレクトリに配置

* https://moji.or.jp/ipafont/ipafontdownload/

## 環境変数
発行されたトークンを環境変数にセット
```
$ export SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
$ export SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
$ export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

## 起動
### 通常起動
```
$ uv run slack-app.py
```

自動で以下が行われる
* Python3.12のインストール(利用していなければ)
* 仮想環境の作成
* 依存パッケージのインストール
* スクリプトの起動

### バックグラウンド起動
```
(venvdir) $ nohup uv run slack-app.py > /dev/null 2>&1 &
```

#### 停止
PIDを調べてプロセスをkill。

## その他設定
* [デーモン化](daemonization.md)
