import logging
import os
from flask import Flask, request, jsonify

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/api.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/trendspider', methods=['POST'])
def trendspider():
    data = request.get_json()
    symbol = data.get('symbol')
    category = data.get('category')
    action = data.get('action')
    quantity = data.get('quantity')
    message = jsonify({'message': f'Received trendspider request for {symbol} with category {category}, action {action}, and quantity {quantity}'})
    logging.info({'message': f'Received trendspider request for {symbol} with category {category}, action {action}, and quantity {quantity}'})
    return message

if __name__ == '__main__':
    app.run()
