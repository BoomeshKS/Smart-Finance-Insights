import psycopg2
import bcrypt
import json

DB_URL = "postgresql://neondb_owner:npg_9hDVrMUB4HYP@ep-royal-dawn-ay0i6480-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_conn():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            pwd VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            phone VARCHAR(20),
            address TEXT,
            occupation VARCHAR(100),
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            uid INTEGER REFERENCES users(id) ON DELETE CASCADE,
            cat VARCHAR(100) NOT NULL,
            limit_amount DECIMAL(10,2) NOT NULL,
            month VARCHAR(7) NOT NULL,
            UNIQUE(uid, cat, month)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_fields (
            id SERIAL PRIMARY KEY,
            uid INTEGER REFERENCES users(id) ON DELETE CASCADE,
            field_title VARCHAR(100) NOT NULL,
            field_value TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(uid, field_title)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def reg_user(name, email, pwd):
    conn = get_conn()
    cur = conn.cursor()
    try:
        hpwd = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (name, email, pwd) VALUES (%s,%s,%s) RETURNING id", (name, email, hpwd))
        uid = cur.fetchone()[0]
        conn.commit()
        return True, uid
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def login_user(name, pwd):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, pwd FROM users WHERE name=%s", (name,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and bcrypt.checkpw(pwd.encode(), user[3].encode()):
        return True, {"id": user[0], "name": user[1], "email": user[2]}
    return False, "Invalid credentials"

def create_budget(uid, cat, limit_amount, month):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO budgets (uid, cat, limit_amount, month)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (uid, cat, month)
            DO UPDATE SET limit_amount=EXCLUDED.limit_amount
        """, (uid, cat, limit_amount, month))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def get_budgets(uid, month):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT cat, limit_amount FROM budgets WHERE uid=%s AND month=%s", (uid, month))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def get_all_budgets(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT cat, limit_amount, month FROM budgets WHERE uid=%s ORDER BY month DESC, cat", (uid,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def update_budget(uid, cat, limit_amount, month):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE budgets SET limit_amount=%s 
            WHERE uid=%s AND cat=%s AND month=%s
        """, (limit_amount, uid, cat, month))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def delete_budget(uid, cat, month):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM budgets WHERE uid=%s AND cat=%s AND month=%s", (uid, cat, month))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def get_user_profile(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, email, full_name, phone, address, occupation 
        FROM users WHERE id=%s
    """, (uid,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return {
            "id": user[0], "name": user[1], "email": user[2],
            "full_name": user[3], "phone": user[4], 
            "address": user[5], "occupation": user[6]
        }
    return None

def update_user_profile(uid, full_name, phone, address, occupation):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE users 
            SET full_name=%s, phone=%s, address=%s, occupation=%s
            WHERE id=%s
        """, (full_name, phone, address, occupation, uid))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def get_user_fields(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, field_title, field_value FROM user_fields WHERE uid=%s ORDER BY field_title", (uid,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def add_user_field(uid, field_title, field_value):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO user_fields (uid, field_title, field_value)
            VALUES (%s,%s,%s)
            ON CONFLICT (uid, field_title)
            DO UPDATE SET field_value=EXCLUDED.field_value
        """, (uid, field_title, field_value))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def update_user_field(uid, field_id, field_title, field_value):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE user_fields 
            SET field_title=%s, field_value=%s
            WHERE id=%s AND uid=%s
        """, (field_title, field_value, field_id, uid))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()

def delete_user_field(uid, field_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_fields WHERE id=%s AND uid=%s", (field_id, uid))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()
        conn.close()