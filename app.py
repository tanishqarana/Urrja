from flask import Flask, request, render_template
import requests  # Used to send HTTP requests to ESP32

app = Flask(__name__)

# Route to serve the main webpage
@app.route('/')
def index():
    return render_template("index.html")

# Endpoint to handle commands from the web page
@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json
    command = data.get('command')
    
    # Send the command to the ESP32 over HTTP
    esp_ip = 'http://ESP32_IP_ADDRESS'  # Replace with your ESP32's IP
    response = requests.post(f"{esp_ip}/receive_command", json={"command": command})
    
    return "Command sent!", response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # Accessible from networks