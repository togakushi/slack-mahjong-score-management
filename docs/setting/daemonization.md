# systemdを使ったデーモン化

## 実行環境準備

セットアップ手順を実施し、スクリプトが起動できるようにする
* [uvを使った環境構築](using_uv.md)
* [venvを使った環境構築](using_venv.md)

環境変数を記録したファイルを準備する(app.env)
```
SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

## systemd設定
### unitファイル作成
`/etc/systemd/system/slack-app.service`を作成
```
[Unit]
Description=slack mahjong score management
After=network.target

[Service]
User=<user name>
Type=simple
WorkingDirectory=/path/to/<app-dir>/
EnvironmentFile=/path/to/<app-dir>/app.env
#ExecStartPre=git pull
ExecStart=/path/to/<venv-dir>/bin/python3 /path/to/<app-dir>/slack-app.py --notime
#Restart=always

[Install]
WantedBy=default.target
```
* `User`にスクリプトを起動するユーザ名を指定
* `WorkingDirectory`に指定するディレクトリは`git clone`したときに作成したディレクトリ
* `/path/to/<venv-dir>/bin/python3`は仮想環境のPython
* `/path/to/<app-dir>/app.env`は環境変数を記述したファイル
* `ExecStartPre`、`Restart`はお好みで

### unitファイル反映
```
$ sudo systemctl daemon-reload
```

### 自動起動有効化
```
$ sudo systemctl enable slack-app.service
```

### 起動/停止
```
$ systemctl start slack-app.service
```

```
$ systemctl stop slack-app.service
```

### ログ確認
```
$ systemctl status slack-app.service -l --no-pager
```
```
$ journalctl -l -u slack-app.service --no-pager
```
