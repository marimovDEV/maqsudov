import sqlite3
from contextlib import closing

DB_NAME = 'botdata.db'

def init_db():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        # Mashinalar
        c.execute('''CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )''')
        # Marshrutlar
        c.execute('''CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )''')
        # Foydalanuvchilar
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT,
            phone TEXT
        )''')
        # Buyurtmalar
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            direction TEXT,
            date TEXT,
            phone TEXT,
            trip_type TEXT,
            car TEXT,
            address TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()

# --- CARS ---
def add_car(name):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        try:
            c.execute('INSERT INTO cars (name) VALUES (?)', (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_car(name):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM cars WHERE name=?', (name,))
        conn.commit()

def get_cars():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('SELECT name FROM cars ORDER BY name')
        return [row[0] for row in c.fetchall()]

# --- ROUTES ---
def add_route(name):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        try:
            c.execute('INSERT INTO routes (name) VALUES (?)', (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def remove_route(name):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('DELETE FROM routes WHERE name=?', (name,))
        conn.commit()

def get_routes():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('SELECT name FROM routes ORDER BY name')
        return [row[0] for row in c.fetchall()]

# --- USERS ---
def add_user(user_id, full_name, phone=None):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO users (user_id, full_name, phone) VALUES (?, ?, ?)', (user_id, full_name, phone))
        conn.commit()

def update_user_phone(user_id, phone):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET phone=? WHERE user_id=?', (phone, user_id))
        conn.commit()

def get_user(user_id):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
        return c.fetchone()

def get_users_count():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        return c.fetchone()[0]

# --- ORDERS ---
def add_order(user_id, direction, date, phone, trip_type, car, address, comment):
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO orders (user_id, direction, date, phone, trip_type, car, address, comment) \
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, direction, date, phone, trip_type, car, address, comment))
        conn.commit()

def get_orders():
    with closing(sqlite3.connect(DB_NAME)) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM orders ORDER BY created_at DESC')
        return c.fetchall() 