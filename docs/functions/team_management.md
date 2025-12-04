# チーム管理

## チーム作成/削除
チームの作成/削除はスラッシュコマンドで行う。

### スラッシュコマンド構文
登録
```
/commandname team_create <作成するチーム名>
/commandname team_add <作成するチーム名>
```
削除
```
/commandname team_del <削除するチーム名>
```

## メンバーのチーム所属/離脱

### スラッシュコマンド構文
所属
```
/commandname team_add <所属させるチーム名> <所属するメンバー名>
```
離脱
```
/commandname team_remove <離脱させるチーム名> <離脱するメンバー名>
```

## チーム情報削除
全チームの削除、および全メンバーを未所属にする。

### スラッシュコマンド構文
```
/commandname team_clear
```
