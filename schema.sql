CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    initial_balance REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    buy_price REAL NOT NULL DEFAULT 0,
    expenses REAL NOT NULL DEFAULT 0,
    sell_price REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'в работе',
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS car_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    car_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL DEFAULT 'деталь',
    description TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(car_id) REFERENCES cars(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id)
);