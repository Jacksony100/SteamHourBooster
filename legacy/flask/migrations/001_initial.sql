CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    subscription_end TEXT,
    is_admin INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0,
    last_ip TEXT,
    last_seen TEXT
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    shared_secret TEXT,
    steamid64 TEXT,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER UNIQUE NOT NULL,
    game_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS account_games (
    account_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    PRIMARY KEY (account_id, game_id),
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_account_games_account_id ON account_games(account_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
