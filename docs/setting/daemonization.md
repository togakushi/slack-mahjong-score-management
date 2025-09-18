# systemdを使ったデーモン化

## 実行環境準備

> [!NOTE]
> 【前提条件】セットアップ手順を実施し、スクリプトが起動できるようにする。
> * [uvを使った環境構築](using_uv.md)
> * [venvを使った環境構築](using_venv.md)

環境変数を記録したファイルを準備する(.env)
```
SLACK_APP_TOKEN=xapp-x-xxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_WEB_TOKEN=xoxp-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

## systemd設定
### unitファイル作成
`/etc/systemd/system/python_app.service`を作成(ファイル名は好みでよい)
```
[Unit]
Description=slack mahjong score management
After=network.target

[Service]
User=<user name>
Type=simple
WorkingDirectory=/path/to/<app-dir>/
EnvironmentFile=/path/to/<app-dir>/.env
#ExecStartPre=git pull
ExecStart=/path/to/<venv-dir>/bin/python3 /path/to/<app-dir>/app.py --notime
#Restart=always

[Install]
WantedBy=default.target
```
* `User`にスクリプトを起動するユーザ名を指定
* `WorkingDirectory`に指定するディレクトリは`git clone`したときに作成したディレクトリ
* `/path/to/<venv-dir>/bin/python3`は仮想環境のPython
* `/path/to/<app-dir>/.env`は環境変数を記述したファイル
* `ExecStartPre`、`Restart`はお好みで

### unitファイル反映
```
$ sudo systemctl daemon-reload
```

### 自動起動有効化
```
$ sudo systemctl enable python_app.service
```

### 起動/停止
```
$ systemctl start python_app.service
```

```
$ systemctl stop python_app.service
```

### ログ確認
```
$ systemctl status python_app.service -l --no-pager
```
```
$ journalctl -l -u python_app.service --no-pager
```
