# 利用APIと要求権限

## Bot Token Scopes

|      Scope       |  chat_postMessage  |  files_upload_v2   |   reactions_add    |  reactions_remove  |   reactions_get    | conversations_open |    bot events    |     その他     |
| ---------------- | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :----------------: | :--------------: | :------------: |
| commands         |                    |                    |                    |                    |                    |                    |                  | Slash Commands |
| channels:history |                    |                    |                    |                    |                    |                    | message.channels |                |
| groups:history   |                    |                    |                    |                    |                    |                    |  message.groups  |                |
| chat:write       | :heavy_check_mark: |                    |                    |                    |                    |                    |                  |                |
| files:write      |                    | :heavy_check_mark: |                    |                    |                    |                    |                  |                |
| im:history       |                    |                    |                    |                    |                    |                    |    message.im    |                |
| im:write         |                    |                    |                    |                    |                    | :heavy_check_mark: |                  |                |
| reactions:read   |                    |                    |                    |                    | :heavy_check_mark: |                    |                  |                |
| reactions:write  |                    |                    | :heavy_check_mark: | :heavy_check_mark: |                    |                    |                  |                |
| none             |                    |                    |                    |                    |                    |                    | app_home_opened  |                |

## OAuth Scope

|    Scope    |  search_messages   |
| ----------- | :----------------: |
| search:read | :heavy_check_mark: |
