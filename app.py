from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests

app = Flask(__name__)

# Database setup
DATABASE = 'new_energy_market.db'  # SQLite database file

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    conn.execute('PRAGMA foreign_keys = ON')  # Ensure foreign keys are enabled
    return conn

# Initialize the database (you can also do this manually in SQLite)
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            ip_address TEXT
        );
    ''')
    conn.commit()
    conn.close()

# Call this when the app starts to ensure the table exists
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/save-data', methods=['POST'])
def save_data():
    data = request.json
    users = data.get('users')
    energy_listings = data.get('energyListings')
    
    # Save users and listings to database
    save_users_to_db(users)
    save_energy_listings_to_db(energy_listings)
    
    return jsonify({'status': 'success'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    user = check_user_credentials(username, email, password)
    if user:
        return jsonify({'success': True, 'user': user})
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@app.route('/api/list-energy', methods=['POST'])
def list_energy():
    data = request.json
    energy_amount = data.get('energyAmount')
    price_per_kwh = data.get('pricePerKWh')
    seller_user_id = data.get('sellerUserId')

    # Insert energy listing into DB
    create_energy_listing_in_db(seller_user_id, energy_amount, price_per_kwh)
    return jsonify({'success': True})

@app.route('/api/complete-transaction', methods=['POST'])
def complete_transaction():
    data = request.json
    energy_amount_to_buy = data.get('energyAmountToBuy')
    buyer_user_id = data.get('buyerUserId')

    # Process the transaction in DB
    process_transaction_in_db(buyer_user_id, energy_amount_to_buy)
    return jsonify({'success': True})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if check_if_user_exists(username, email):
        return jsonify({'success': False, 'error': 'Username or email already exists'})

    # Create new user in DB
    create_user_in_db(username, email, password)
    return jsonify({'success': True})

def create_user_in_db(username, email, password):
    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO users (username, email, password) 
        VALUES (?, ?, ?)
    ''', (username, email, hashed_password))
    conn.commit()
    conn.close()

def check_user_credentials(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND email = ?', (username, email))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        return {'user_id': user['user_id'], 'username': user['username'], 'email': user['email']}
    return None

def check_if_user_exists(username, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def save_users_to_db(users):
    conn = get_db_connection()
    for user in users:
        hashed_password = generate_password_hash(user['password'])
        conn.execute('''
            INSERT INTO users (username, email, password) 
            VALUES (?, ?, ?)
        ''', (user['username'], user['email'], hashed_password))
    conn.commit()
    conn.close()

def save_energy_listings_to_db(energy_listings):
    conn = get_db_connection()
    for listing in energy_listings:
        conn.execute('''
            INSERT INTO energy_listings (seller_user_id, energy_amount, price_per_kwh) 
            VALUES (?, ?, ?)
        ''', (listing['seller_user_id'], listing['energy_amount'], listing['price_per_kwh']))
    conn.commit()
    conn.close()

def create_energy_listing_in_db(seller_user_id, energy_amount, price_per_kwh):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO energy_listings (seller_user_id, energy_amount, price_per_kwh) 
        VALUES (?, ?, ?)
    ''', (seller_user_id, energy_amount, price_per_kwh))
    conn.commit()
    conn.close()

def process_transaction_in_db(buyer_user_id, energy_amount_to_buy):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM energy_listings WHERE energy_amount >= ?', (energy_amount_to_buy,))
    listing = cursor.fetchone()

    if listing:
        conn.execute('''
            INSERT INTO transactions (buyer_user_id, seller_user_id, listing_id, transaction_amount) 
            VALUES (?, ?, ?, ?)
        ''', (buyer_user_id, listing['seller_user_id'], listing['listing_id'], energy_amount_to_buy))

        # Update the energy listing
        new_energy_amount = listing['energy_amount'] - energy_amount_to_buy
        conn.execute('''
            UPDATE energy_listings 
            SET energy_amount = ? 
            WHERE listing_id = ?
        ''', (new_energy_amount, listing['listing_id']))

        conn.commit()
    else:
        # Handle case where no matching listing is found
        pass
    conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
