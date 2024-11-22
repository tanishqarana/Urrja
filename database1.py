import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect('new_energy_market.db')
cursor = conn.cursor()

# SQL Statements to create tables
create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

create_energy_listings_table = """
CREATE TABLE IF NOT EXISTS energy_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
"""

create_transactions_table = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_user_id INTEGER,
    seller_user_id INTEGER,
    listing_id INTEGER,
    transaction_amount REAL NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (buyer_user_id) REFERENCES users (user_id),
    FOREIGN KEY (seller_user_id) REFERENCES users (user_id),
    FOREIGN KEY (listing_id) REFERENCES energy_listings (listing_id)
);
"""

create_ip_address_logs_table = """
CREATE TABLE IF NOT EXISTS ip_address_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ip_address TEXT NOT NULL,
    log_type TEXT DEFAULT 'Login',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);
"""
# Execute each create table command
cursor.execute(create_users_table)
cursor.execute(create_energy_listings_table)
cursor.execute(create_transactions_table)
cursor.execute(create_ip_address_logs_table)


# Commit changes and close connection
conn.commit()
conn.close()

print("Tables created successfully!")
