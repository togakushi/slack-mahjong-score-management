create table if not exists "member" (
    "id"        INTEGER,
    "name"      TEXT NOT NULL UNIQUE,
    "slack_id"  TEXT,
    "team_id"   INTEGER,
    "flying"    INTEGER DEFAULT 0,
    "reward"    INTEGER DEFAULT 0,
    "abuse"     INTEGER DEFAULT 0,
    PRIMARY KEY("id" AUTOINCREMENT)
);
