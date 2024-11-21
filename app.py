from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Endpoint to simulate energy purchase
@app.route('/buy-energy', methods=['POST'])
def buy_energy():
    data = request.json
    buyer_ip = data.get('buyerIp')
    seller_ip = data.get('sellerIp')
    price_per_unit = data.get('price')

    if not (buyer_ip and seller_ip and price_per_unit):
        return jsonify({"error": "Invalid data"}), 400

    # Log the received data for debugging
    app.logger.info(f"Buyer IP: {buyer_ip}, Seller IP: {seller_ip}, Price: {price_per_unit}")

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
            return jsonify({"status": "Energy transfer started"}), 200
        else:
            return jsonify({"error": f"ESP returned status {response.status_code}"}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"ESP communication error: {e}")
        return jsonify({"error": "Failed to initiate transfer on ESP"}), 500
