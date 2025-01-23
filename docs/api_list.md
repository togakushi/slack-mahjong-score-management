# 利用APIと要求権限

## Bot Token Scopes

|      Scope       | chat_postMessage | files_upload_v2 | reactions_add | reactions_remove | reactions_get | conversations_open |    bot events    |     その他     |
| ---------------- | :--------------: | :-------------: | :-----------: | :--------------: | :-----------: | :----------------: | :--------------: | :------------: |
| commands         |                  |                 |               |                  |               |                    |                  | Slash Commands |
| channels:history |                  |                 |               |                  |               |                    | message.channels |                |
| chat:write       |        o         |                 |               |                  |               |                    |                  |                |
| files:write      |                  |        o        |               |                  |               |                    |                  |                |
| im:history       |                  |                 |               |                  |               |                    |    message.im    |                |
| im:write         |                  |                 |               |                  |               |         o          |                  |                |
| reactions:read   |                  |                 |               |                  |       o       |                    |                  |                |
| reactions:write  |                  |                 |       o       |        o         |               |                    |                  |                |
| none             |                  |                 |               |                  |               |                    | app_home_opened  |                |

## OAuth Scope

|    Scope    | search_messages |
| ----------- | :-------------: |
| search:read |        o        |
