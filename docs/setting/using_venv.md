# venvを使った実行環境構築
Python3.12以上の実行環境が必要なため、OS環境に合わせて準備する。

> [!TIP]
> インストールが必要な環境なのであれば[uvの利用](using_uv.md)がおすすめ。

## 本体インストール
```
$ git clone https://github.com/togakushi/slack-mahjong-score-management.git
```

## 仮想環境の作成
作成するディレクトリ名は任意。

```
$ python3 -m venv venvdir
$ source ./venvdir/bin/activate
```

## 依存パッケージのインストール
```
(venvdir) $ cd slack-mahjong-score-management
(venvdir) $ pip install -U pip
(venvdir) $ pip install -r requirements.txt
```

## グラフ描写用の日本語フォント
IPAexフォント（ipaexg.ttf）を `slack-app.py` と同じディレクトリに配置

* https://moji.or.jp/ipafont/ipafontdownload/


## 起動
発行されたトークンを環境変数にセット
```
(venvdir) $ export SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venvdir) $ export SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
(venvdir) $ export SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

### 動かしっぱなしにする
```
(venvdir) $ nohup python3 slack-app.py -c config.ini > /dev/null 2>&1 &
```

### 停止
PIDを調べてプロセスをkill。
