# 利用APIと要求権限

## Bot Token Scopes

|      Scope       |  chat_postMessage  |  files_upload_v2   | reactions_add<br>reactions_remove |   reactions_get    | conversations_open | conversations_replies |    bot events    |     その他     |
| ---------------- | :----------------: | :----------------: | :-------------------------------: | :----------------: | :----------------: | :-------------------: | :--------------: | :------------: |
| commands         |                    |                    |                                   |                    |                    |                       |                  | Slash Commands |
| channels:history |                    |                    |                                   |                    |                    |  :heavy_check_mark:   | message.channels |                |
| groups:history   |                    |                    |                                   |                    |                    |  :heavy_check_mark:   |  message.groups  |                |
| chat:write       | :heavy_check_mark: |                    |                                   |                    |                    |                       |                  |                |
| files:write      |                    | :heavy_check_mark: |                                   |                    |                    |                       |                  |                |
| im:history       |                    |                    |                                   |                    |                    |  :heavy_check_mark:   |    message.im    |                |
| im:write         |                    |                    |                                   |                    | :heavy_check_mark: |                       |                  |                |
| reactions:read   |                    |                    |                                   | :heavy_check_mark: |                    |                       |                  |                |
| reactions:write  |                    |                    |        :heavy_check_mark:         |                    |                    |                       |                  |                |
| none             |                    |                    |                                   |                    |                    |                       | app_home_opened  |                |

## OAuth Scope

|    Scope    |  search_messages   |
| ----------- | :----------------: |
| search:read | :heavy_check_mark: |
