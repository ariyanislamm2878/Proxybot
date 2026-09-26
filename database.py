import os

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = False
conn = None
c = None

if DATABASE_URL:
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        c = conn.cursor()
        USE_POSTGRES = True
        print("✅ PostgreSQL Connected")
    except Exception as e:
        print(f"Postgres error {e}")
        USE_POSTGRES = False

if not USE_POSTGRES:
    import sqlite3
    conn = sqlite3.connect("proxystore.db", check_same_thread=False)
    c = conn.cursor()
    print("⚠ Using SQLite")

def init_db():
    if USE_POSTGRES:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            balance FLOAT DEFAULT 0,
            referred_by BIGINT DEFAULT NULL,
            referral_count INT DEFAULT 0,
            total_referral_earning FLOAT DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            product TEXT,
            price FLOAT,
            status TEXT DEFAULT 'Approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS stock (
            id SERIAL PRIMARY KEY,
            category TEXT,
            product_name TEXT,
            code TEXT,
            status TEXT DEFAULT 'available')''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT,
            referred_id BIGINT UNIQUE,
            status TEXT DEFAULT 'pending')''')
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            referred_by INTEGER DEFAULT NULL,
            referral_count INTEGER DEFAULT 0,
            total_referral_earning REAL DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product TEXT,
            price REAL,
            status TEXT DEFAULT 'Approved')''')
        c.execute('''CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            product_name TEXT,
            code TEXT,
            status TEXT DEFAULT 'available')''')
        c.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            status TEXT DEFAULT 'pending')''')
    conn.commit()

init_db()

def create_user(user_id, referred_by=None):
    try:
        if USE_POSTGRES:
            c.execute("INSERT INTO users (user_id, referred_by) VALUES (%s,%s) ON CONFLICT (user_id) DO NOTHING", (user_id, referred_by))
        else:
            c.execute("INSERT OR IGNORE INTO users (user_id, referred_by) VALUES (?,?)", (user_id, referred_by))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"create_user error: {e}")

def get_balance(user_id):
    try:
        if USE_POSTGRES:
            c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
        else:
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        r = c.fetchone()
        return float(r[0]) if r else 0.0
    except Exception as e:
        conn.rollback()
        return 0.0

def update_balance(user_id, amount):
    create_user(user_id)
    try:
        if USE_POSTGRES:
            c.execute("UPDATE users SET balance = balance + %s WHERE user_id=%s", (amount, user_id))
        else:
            c.execute("UPDATE users SET balance = balance +? WHERE user_id=?", (amount, user_id))
        conn.commit()
    except:
        conn.rollback()

def add_order(user_id, product, price):
    try:
        if USE_POSTGRES:
            c.execute("INSERT INTO orders (user_id, product, price, status) VALUES (%s,%s,%s,%s) RETURNING id", (user_id, product, price, "Approved"))
            oid = c.fetchone()[0]
        else:
            c.execute("INSERT INTO orders (user_id, product, price, status) VALUES (?,?,?,?)", (user_id, product, price, "Approved"))
            oid = c.lastrowid
        conn.commit()
        return oid
    except:
        conn.rollback()
        return None

def get_orders(user_id):
    try:
        if USE_POSTGRES:
            c.execute("SELECT product, price, status FROM orders WHERE user_id=%s ORDER BY id DESC", (user_id,))
        else:
            c.execute("SELECT product, price, status FROM orders WHERE user_id=? ORDER BY id DESC", (user_id,))
        return c.fetchall()
    except:
        conn.rollback()
        return []

def get_order_by_id(order_id):
    try:
        if USE_POSTGRES:
            c.execute("SELECT id, user_id, product, price, status FROM orders WHERE id=%s", (order_id,))
        else:
            c.execute("SELECT id, user_id, product, price, status FROM orders WHERE id=?", (order_id,))
        return c.fetchone()
    except:
        conn.rollback()
        return None

def update_order_status(order_id, status):
    try:
        if USE_POSTGRES:
            c.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
        else:
            c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        conn.commit()
    except:
        conn.rollback()

def get_all_users():
    try:
        c.execute("SELECT user_id FROM users")
        return [u[0] for u in c.fetchall()]
    except:
        conn.rollback()
        return []

def add_stock(category, product_name, codes_list):
    try:
        for code in codes_list:
            if code.strip():
                if USE_POSTGRES:
                    c.execute("INSERT INTO stock (category, product_name, code) VALUES (%s,%s,%s)", (category, product_name, code.strip()))
                else:
                    c.execute("INSERT INTO stock (category, product_name, code) VALUES (?,?,?)", (category, product_name, code.strip()))
        conn.commit()
    except:
        conn.rollback()

def get_stock_count(category, product_name):
    try:
        if USE_POSTGRES:
            c.execute("SELECT COUNT(*) FROM stock WHERE category=%s AND product_name=%s AND status='available'", (category, product_name))
        else:
            c.execute("SELECT COUNT(*) FROM stock WHERE category=? AND product_name=? AND status='available'", (category, product_name))
        return c.fetchone()[0]
    except:
        conn.rollback()
        return 0

def take_codes(category, product_name, qty):
    try:
        if USE_POSTGRES:
            c.execute("SELECT id, code FROM stock WHERE category=%s AND product_name=%s AND status='available' LIMIT %s", (category, product_name, qty))
        else:
            c.execute("SELECT id, code FROM stock WHERE category=? AND product_name=? AND status='available' LIMIT?", (category, product_name, qty))
        rows = c.fetchall()
        codes = []
        for r in rows:
            if USE_POSTGRES:
                c.execute("UPDATE stock SET status='used' WHERE id=%s", (r[0],))
            else:
                c.execute("UPDATE stock SET status='used' WHERE id=?", (r[0],))
            codes.append(r[1])
        conn.commit()
        return codes
    except Exception as e:
        conn.rollback()
        return []

def add_referral(referrer_id, referred_id):
    if referrer_id == referred_id: return
    try:
        if USE_POSTGRES:
            c.execute("INSERT INTO referrals (referrer_id, referred_id) VALUES (%s,%s) ON CONFLICT (referred_id) DO NOTHING", (referrer_id, referred_id))
        else:
            c.execute("INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?,?)", (referrer_id, referred_id))
        conn.commit()
    except:
        conn.rollback()

def activate_referral_bonus(referred_id, deposit_amount=0):
    if deposit_amount < 10:
        return None
    try:
        if USE_POSTGRES:
            c.execute("SELECT referrer_id FROM referrals WHERE referred_id=%s AND status='pending'", (referred_id,))
        else:
            c.execute("SELECT referrer_id FROM referrals WHERE referred_id=? AND status='pending'", (referred_id,))
        res = c.fetchone()
        if res:
            referrer_id = res[0]
            if referrer_id == referred_id: return None
            update_balance(referrer_id, 0.50)
            if USE_POSTGRES:
                c.execute("UPDATE users SET referral_count = referral_count + 1, total_referral_earning = total_referral_earning + 0.50 WHERE user_id=%s", (referrer_id,))
                c.execute("UPDATE referrals SET status='active' WHERE referred_id=%s", (referred_id,))
            else:
                c.execute("UPDATE users SET referral_count = referral_count + 1, total_referral_earning = total_referral_earning + 0.50 WHERE user_id=?", (referrer_id,))
                c.execute("UPDATE referrals SET status='active' WHERE referred_id=?", (referred_id,))
            conn.commit()
            return referrer_id
        return None
    except:
        conn.rollback()
        return None

def get_refer_stats(user_id):
    try:
        if USE_POSTGRES:
            c.execute("SELECT referral_count, total_referral_earning FROM users WHERE user_id=%s", (user_id,))
        else:
            c.execute("SELECT referral_count, total_referral_earning FROM users WHERE user_id=?", (user_id,))
        data = c.fetchone()
        return data if data else (0, 0.0)
    except:
        conn.rollback()
        return (0, 0.0)

# --- FIXED PART ---
def get_all_stock():
    try:
        if USE_POSTGRES:
            c.execute("SELECT category, product_name, COUNT(*) FROM stock WHERE status='available' GROUP BY category, product_name")
        else:
            c.execute("SELECT category, product_name, COUNT(*) FROM stock WHERE status='available' GROUP BY category, product_name")
        return c.fetchall()
    except Exception as e:
        conn.rollback()
        print(f"get_all_stock error: {e}")
        return []
