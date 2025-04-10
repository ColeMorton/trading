from pybit.unified_trading import HTTP
# import os
# import json
# import hmac
# import hashlib
# import time

# def get_bybit_payload(body):
#     symbol = body.get('symbol')
#     category = body.get('category')
#     action = body.get('action')
#     quantity = body.get('quantity')
    
#     if action == 'buy':
#         side = 'Buy'
#     elif action == 'sell':
#         side = 'Sell'
#     else:
#         raise ValueError("Invalid action: must be 'buy' or 'sell'")
    
#     return {
#         'symbol': symbol,
#         'category': category,
#         'side': side,
#         'orderType': 'Market',
#         'qty': quantity
#     }

# def send_bybit_request(params):
#     # Accessing environment variables
#     api_key = os.getenv('BYBIT_API_KEY')
#     api_secret = os.getenv('BYBIT_API_SECRET')  
    
#     is_prod = os.getenv('PROD')
    
#     # Create a session with the Bybit API
#     session = HTTP(api_key=api_key, api_secret=api_secret, testnet=True)
    
#     try:
#         response = session.place_order(params)
#         raise ValueError(f"Bybit order response: {response}")
#     except Exception as e:
#         raise ValueError(f"Bybit order error occurred: {response}")
    
#     # params['timestamp'] = str(int(time.time() * 1000))
    
#     # if is_prod:
#     #     url = 'https://api.bybit.com/v2/private/order/create'
#     # else:
#     #     url = 'https://api-demo.bybit.com/v2/private/order/create'
    
#     # Create a signature
#     # query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
#     # signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
#     # Add signature to parameters
#     # params['sign'] = signature
    
#     # Send the request to Bybit API
#     # response = requests.post(url, data=params)
    
#     # Log the response
#     # print(json.dumps(response.json()))
    
#     # return {
#     #     'statusCode': response.status_code,
#     #     'body': json.dumps(response.json())
#     # }
    
#     # # Respond with the result
#     # return {
#     #     'statusCode': 200,
#     #     'body': json.dumps(result)
#     # }
