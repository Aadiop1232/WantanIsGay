import sqlite3
import os
from datetime import datetime
import json
import config
from handlers.logs import log_event

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bot.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DATABASE)

def init_db():
    """Initializes the database and creates necessary tables."""
    conn = get_connection()
    c = conn.cursor()

    # Create users table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        telegram_id TEXT PRIMARY KEY,
        username TEXT,
        join_date TEXT,
        points INTEGER DEFAULT 20,
        referrals INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        pending_referrer TEXT,
        verified INTEGER DEFAULT 0
    )
    ''')

    # Create referrals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            user_id TEXT,
            referred_id TEXT,
            PRIMARY KEY (user_id, referred_id)
        )
    ''')

    # Create platforms table
    c.execute('''
        CREATE TABLE IF NOT EXISTS platforms (
            platform_name TEXT PRIMARY KEY,
            stock TEXT,
            price INTEGER DEFAULT {config.DEFAULT_ACCOUNT_CLAIM_COST},
            platform_type TEXT DEFAULT 'account'
        )
    ''')

    # Create reports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            report_text TEXT,
            status TEXT DEFAULT 'open',
            claimed INTEGER DEFAULT 0,
            claimed_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            review TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create admin_logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id TEXT,
            action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create channels table
    c.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_link TEXT
        )
    ''')

    # Create admins table
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            role TEXT,
            banned INTEGER DEFAULT 0
        )
    ''')

    # Create keys table
    c.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            "key" TEXT PRIMARY KEY,
            type TEXT,
            points INTEGER,
            claimed INTEGER DEFAULT 0,
            claimed_by TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create configurations table
    c.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            config_key TEXT PRIMARY KEY,
            config_value TEXT
        )
    ''')

    conn.commit()
    c.close()
    conn.close()

def get_user(telegram_id):
    """Fetch user details from the database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    c.close()
    conn.close()
    return dict(user) if user else None

def add_user(telegram_id, username, join_date, pending_referrer=None):
    """Add a new user to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    if not user:
        c.execute("""
            INSERT INTO users (telegram_id, username, join_date, pending_referrer)
            VALUES (?, ?, ?, ?)
        """, (telegram_id, username, join_date, pending_referrer))
        conn.commit()
    c.close()
    conn.close()
    return get_user(telegram_id)

def update_user_points(telegram_id, new_points):
    """Update a user's points."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET points = ? WHERE telegram_id = ?", (new_points, telegram_id))
    conn.commit()
    c.close()
    conn.close()

def update_user_verified(telegram_id):
    """Mark a user as verified."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET verified = 1 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    c.close()
    conn.close()

def get_report_by_id(report_id):
    """Fetch a report by its ID."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = c.fetchone()
    c.close()
    conn.close()
    return dict(report) if report else None

def claim_report_by_admin(admin_id, report_id):
    """Mark a report as claimed by an admin."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE reports SET claimed = 1, claimed_by = ? WHERE id = ?", (admin_id, report_id))
    conn.commit()
    c.close()
    conn.close()

def close_report_in_db(report_id):
    """Close a report in the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE reports SET status = 'closed' WHERE id = ?", (report_id,))
    conn.commit()
    c.close()
    conn.close()

def add_review(user_id, review_text):
    """Add a review to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO reviews (user_id, review, timestamp) VALUES (?, ?, ?)", (user_id, review_text, datetime.now()))
    conn.commit()
    c.close()
    conn.close()

def get_platforms():
    """Fetch all platforms."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM platforms")
    platforms = c.fetchall()
    c.close()
    conn.close()
    return [dict(p) for p in platforms]

def get_leaderboard(limit=10):
    """Fetch the points leaderboard."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT telegram_id, username, points FROM users ORDER BY points DESC LIMIT ?", (limit,))
    leaderboard = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in leaderboard]

def get_referral_leaderboard(limit=10):
    """Fetch the referral leaderboard."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT u.telegram_id, u.username, COUNT(r.referred_id) AS referrals
        FROM users u
        LEFT JOIN referrals r ON u.telegram_id = r.user_id
        GROUP BY u.telegram_id
        ORDER BY referrals DESC
        LIMIT ?
    """, (limit,))
    leaderboard = c.fetchall()
    c.close()
    conn.close()
    return [dict(row) for row in leaderboard]

def update_stock_for_platform(platform_name, stock):
    """Update the stock for a platform."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE platforms SET stock = ? WHERE platform_name = ?", (json.dumps(stock), platform_name))
    conn.commit()
    c.close()
    conn.close()
    log_event(telebot.TeleBot(config.TOKEN), "stock", f"Platform '{platform_name}' stock updated to {len(stock)} items.")

def get_platform_by_name(platform_name):
    """Fetch a platform by name."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM platforms WHERE platform_name = ?", (platform_name,))
    platform = c.fetchone()
    c.close()
    conn.close()
    return dict(platform) if platform else None
