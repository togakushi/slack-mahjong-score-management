# インターフェース
```mermaid
---
config:
  flowchart:
    curve: linear
---
flowchart TB
    event(event handler);
    m1[["MessageParser(data)"]];

    event --> m1 --> d["dispatcher()"] --> f1 & f2 & f3 & f4;

    subgraph f1[Sub command]
        direction TB
        c([command]) --> sc1 & sc2 & sc3 & sc4;
        sc1(results) --> cp1[[CommandParser]] --> p1(aggregation);
        sc2(graph) --> cp2[[CommandParser]] --> p2(aggregation);
        sc3(ranking) --> cp3[[CommandParser]] --> p3(aggregation);
        sc4(report) --> cp4[[CommandParser]] --> p4(aggregation);
        p1 & p2 & p3 & p4 --> mp1[["MessageParser(post)<br>MessageParser(status)"]] --> pp1["post_processing()"];
    end

    subgraph f2[Results record]
        direction TB
        r2([record]);
        r2 --> a1(score) --> results[(results)];
        r2 --> a2(remark) --> remarks[(remarks)];
        results & remarks --> mp2[["MessageParser(post)<br>MessageParser(status)"]] --> pp2["post_processing()"];
    end

    subgraph f3[Member management]
        direction TB
        r1([registry]);
        r1 --> a4(team) --> db2[(team)] & db1;
        r1 --> a3(member) --> db1[(member)] & db3[(alias)];
        r1 --> a5(alias) --> db3;
        db1 & db2 & db3  --> mp3[["MessageParser(post)<br>MessageParser(status)"]];
    end

    subgraph f4[Others]
        direction TB
        h([help]) --> mp4[["MessageParser(post)<br>MessageParser(status)"]];
    end

    f1 & f2 & f3 & f4 --> post["post()<br>(API Interface)"];
```

# アダプタ

アプリ起動時に指定されたサービスのアダプタが設定される。<br>
アダプタは以下のクラスを含む抽象化されたクラスである。

- IntegrationsConfig
- APIInterface
- FunctionsInterface
- MessageParser

<details>
<summary>関係図</summary>

```mermaid
classDiagram
    class ServiceAdapter
        ServiceAdapter : interface_type
        ServiceAdapter --* IntegrationsConfig
        ServiceAdapter --* APIInterface
        ServiceAdapter --* FunctionsInterface
        ServiceAdapter --* MessageParser

    class IntegrationsConfig
        IntegrationsConfig : config_file
        IntegrationsConfig : slash_command
        IntegrationsConfig : badge_degree
        IntegrationsConfig : badge_status
        IntegrationsConfig : badge_grade
        IntegrationsConfig : plotting_backend
        IntegrationsConfig : read_file()

    class APIInterface
        APIInterface : post()

    class FunctionsInterface
        FunctionsInterface : post_processing()
        FunctionsInterface : get_conversations()

    class MessageParser
        MessageParser : data
        MessageParser : post
        MessageParser : status
        MessageParser : parser()

    class MessageParserDataMixin
        MessageParserDataMixin <|-- MessageParser
        MessageParserDataMixin : data
        MessageParserDataMixin : post
        MessageParserDataMixin : status
        MessageParserDataMixin : reset()
        MessageParserDataMixin : get_score()
        MessageParserDataMixin : get_remarks()
```

</details>


## IntegrationsConfig

指定サービスのみで利用する設定値を保存する。<br>
設定値は設定ファイルのサービス名と同じセクションに記述する。

## APIInterface

指定サービスに対して出力を行う。<br>
出力する内容は`MessageParser`の`post`データクラスが保持している。


## FunctionsInterface

指定サービスに対するサービス専用の関数群。

`APIInterface`、`MessageParser`から利用される。

## MessageParser

MessageParserは指定サービスから入力されたテキストデータをコマンドと引数に分ける役割を担う。<br>
状態を保持するためのデータクラスを3つ持つ。

- data
- post
- status

### data

入力されたテキストデータの情報を保持する。

- 入力テキスト
- イベント発生タイムスタンプ
- その他

### post

各機能で集計した結果など、出力するデータを保持する。

- 集計結果
- 生成ファイル
- メッセージデータ
  - 集計期間などの補助情報
- その他

### status

各機能の最終的なステータス情報を保持する。

- DBに対する操作
- 更新したデータの状態
  - 矛盾したデータで更新した、など
- 処理結果
- その他

# ディスパッチャー

各機能はディスパッチテーブルから呼び出される。<br>
呼び出される機能は`MessageParser`を引数に取る。必要な情報は`data`データクラスから取得する。

呼び出された機能はそれぞれ必要な処理を実施し、結果を`post`データクラスと`status`データクラスに保存する。<br>
サービス単位で後処理があるものは`FunctionsInterface`の`post_processing()`で処理する。
