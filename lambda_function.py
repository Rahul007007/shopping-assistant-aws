import json
from agent import Agent
from utils.complete_purchase import complete_purchase
agent = Agent()

def lambda_handler(event, context):
    # Parse the request body correctly
    try:
        body = json.loads(event['body']) if 'body' in event else event
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON format'})
        }
    # Extract values from parsed body
    user_query = body.get('user_query')

    if "complete_purchase" in body and body["complete_purchase"] == True:
        session_id = body.pop("session_id")
        body.pop("complete_purchase")
        purchase_response = complete_purchase(**body)
        return {
            'statusCode': 200,
            'body': json.dumps({'user_query': user_query, 'response': purchase_response, 'tools_used': [], 'session_id': session_id})
        }
    
    agent_response = agent.run(body)
    return {
        'statusCode': 200,
        'body': json.dumps({'user_query': user_query, 'response': agent_response.get("response"), 'tools_used': agent_response.get("tools_used"), 'session_id': agent_response.get("session_id")})
    }
