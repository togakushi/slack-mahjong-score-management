# チーム管理
チームの管理はスラッシュコマンドで行う。
> [!NOTE]
> `/commandname`は[サービス個別設定](../config/integrations.md)の`slash_command`で定義したもの。

## チーム作成
```
/commandname team_create <作成するチーム名>
```
or
```
/commandname team_add <作成するチーム名>
```

> [!WARNING]
> メンバー名と同一のチーム名は登録できない。

## チーム削除
```
/commandname team_del <削除するチーム名>
```

## メンバーのチーム所属
```
/commandname team_add <所属させるチーム名> <所属するメンバー名>
```

> [!IMPORTANT]
> レギュラーメンバーのみがチームに所属できる。

## メンバーのチーム離脱
```
/commandname team_remove <離脱させるチーム名> <離脱するメンバー名>
```

## チーム情報削除
全チームの削除、および全メンバーを未所属に変更する。
```
/commandname team_clear
```
