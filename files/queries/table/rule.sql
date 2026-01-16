create table if not exists "rule" (
    "rule_version"      TEXT NOT NULL UNIQUE,
    "mode"              INTEGER DEFAULT 4,
    "origin_point"      INTEGER DEFAULT 250,
    "return_point"      INTEGER DEFAULT 300,
    "rank_point"        TEXT DEFAULT "30 10 -10 -30",
    "ignore_flying"     INTEGER DEFAULT 0,
    "draw_split"        INTEGER DEFAULT 0,
    PRIMARY KEY("rule_version")
);
