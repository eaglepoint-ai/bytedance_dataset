DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
  id        INTEGER PRIMARY KEY,
  balance   INTEGER NOT NULL CHECK (balance >= 0)
);

INSERT INTO accounts (id, balance) VALUES
  (1, 1000),
  (2, 1000),
  (3, 1000);
