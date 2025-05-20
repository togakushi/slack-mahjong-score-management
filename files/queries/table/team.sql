create table if not exists "team" (
    "id"        INTEGER,
    "name"      TEXT NOT NULL UNIQUE,
    PRIMARY KEY("id" AUTOINCREMENT)
);
