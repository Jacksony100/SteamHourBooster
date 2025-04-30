# Файл: auth.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = 'steam_accounts.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            subscription INTEGER DEFAULT 0,
            sub_end DATE DEFAULT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    db.commit()

def register_user(username, password):
    db = get_db()
    hashed_pw = generate_password_hash(password)
    try:
        db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if user and check_password_hash(user['password'], password):
        return dict(user)
    return None