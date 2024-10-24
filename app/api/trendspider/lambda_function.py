import os
import json
from validation import validate_requester, validate_request, validate_exchange
from bybit import get_bybit_payload, send_bybit_request

def lambda_handler(event, context):
    try:
        print(f"Received event: {json.dumps(event)}")
        
        validate_requester(event)

        body = json.loads(event['body']) if 'body' in event else {}
        validate_request(body)
        
        exchange = validate_exchange(body)
        print(f"exchange: {exchange}")
        
        result = { 'statusCode': 500 }
        
        if exchange == 'bybit':
            payload = get_bybit_payload(body)
            result = send_bybit_request(payload)
        else:
            raise ValueError("No exchange determined")
        
        print(f"Processed result: {result}")
        
        return result

    except Exception as e:
        # Return error response for debugging
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }