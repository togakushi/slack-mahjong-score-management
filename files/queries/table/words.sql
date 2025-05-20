create table if not exists "words" (
    "word"     TEXT NOT NULL UNIQUE,
    "type"     INTEGER,
    "ex_point" INTEGER
);
