from flask import Flask, request, jsonify, render_template
import sqlite3
import requests

app = Flask(__name__)

# Database setup
DATABASE = 'energy_market.db'  # SQLite database file

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
    ''')
    conn.commit()
    conn.close()

# Call this when the app starts to ensure the table exists
init_db()

@app.route('/')
def home():
    return render_template('index.html')

# Endpoint to simulate energy purchase
@app.route('/buy-energy', methods=['POST'])
def buy_energy():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    buyer_ip = data.get('buyerIp')
    seller_ip = data.get('sellerIp')
    price_per_unit = data.get('price')

    if not (buyer_ip and seller_ip and price_per_unit):
        return jsonify({"error": "Invalid or missing data"}), 400

    # Get user IDs for buyer and seller (You may need to look up user info from the users table)
    buyer_user_id = get_user_id_from_ip(buyer_ip)
    seller_user_id = get_user_id_from_ip(seller_ip)

    if not (buyer_user_id and seller_user_id):
        return jsonify({"error": "User not found"}), 404

    # Insert transaction data into the database
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO transactions (buyer_user_id, seller_user_id, transaction_amount) 
            VALUES (?, ?, ?)
        ''', (buyer_user_id, seller_user_id, price_per_unit))
        conn.commit()
        conn.close()

        app.logger.info(f"Stored transaction: Buyer User ID: {buyer_user_id}, Seller User ID: {seller_user_id}, Price: {price_per_unit}")
    except Exception as e:
        app.logger.error(f"Error saving transaction to database: {e}")
        return jsonify({"error": "Failed to save transaction to database"}), 500

    # Send data to ESP32 to start the transfer
    esp_url = f"http://{seller_ip}/start"
    esp_data = {
        "sendIp": seller_ip,
        "receiveIp": buyer_ip,
        "price": price_per_unit
    }

    try:
        response = requests.post(esp_url, json=esp_data, timeout=5)

        if response.status_code == 200:
            app.logger.info("Energy transfer initiated successfully.")
            return jsonify({"status": "Energy transfer started"}), 200
        else:
            app.logger.warning(f"ESP returned status {response.status_code}: {response.text}")
            return jsonify({"error": f"ESP returned status {response.status_code}"}), 500

    except requests.exceptions.RequestException as e:
        app.logger.error(f"ESP communication error: {e}")
        return jsonify({"error": "Failed to initiate transfer on ESP"}), 500


def get_user_id_from_ip(ip_address):
    """
    Function to look up user ID from IP address in the users table.
    You can implement this based on your specific user registration logic.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE ip_address = ?', (ip_address,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user['user_id']
    return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
