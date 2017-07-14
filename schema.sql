DROP TABLE if EXISTS entries;
CREATE TABLE entries(
  id INTEGER PRIMARY KEY autoincrement,
  title text NOT NULL ,
  content text NOT NULL
);