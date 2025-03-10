import boto3
import traceback
def get_order_details(order_id: int):
    """Get all messages from DDB"""
        # Store in DynamoDB
    try:
        dynamodb = boto3.client('dynamodb')
        
        response = dynamodb.get_item(
                        TableName='orders',
                        Key={'order_id': {'N': str(order_id)}}
                        )

        # Extract messages
        item = response.get('Item', {})
        if not item:
            item = f"Order ID: {order_id} not found! Please check the order ID and try again."
        return item
    except Exception as e:
        traceback.print_exc()
        raise e