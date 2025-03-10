import random
import boto3
from decimal import Decimal

# def complete_purchase(total_price: float, cart_items: list):
#     """Generates a short order ID and tracking ID, then confirms order placement."""
#     order_id = str(random.randint(1000, 9999))
#     tracking_id = str(random.randint(100000, 999999))
#     product_ids_str =""
#     for cart_item in cart_items:
#         product_ids_str+=str(cart_item['product_id'])+" "
#     return f"Order has been placed successfully! Order ID: {order_id}, Tracking ID: {tracking_id}. Product IDs are {product_ids_str}"



def complete_purchase(total_price: float, cart_items: list):
    """Generates a short order ID and tracking ID, then confirms order placement and stores in the orders table for future reference."""
    # Generate order and tracking IDs
    order_id = random.randint(1000, 9999)
    tracking_id = str(random.randint(100000, 999999))
    
    # Extract product IDs as a list
    product_ids = [str(cart_item['product_id']) for cart_item in cart_items]
    product_ids_str = " ".join(product_ids)  # Only for display in return message
    
    # Store in DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('orders')
        
        # Insert the order into DynamoDB
        table.put_item(
            Item={
                'order_id': order_id,
                'tracking_id': tracking_id,
                'product_ids': product_ids,  # Storing as a list directly
                'total_cost': Decimal(str(total_price))  # Convert float to Decimal for DynamoDB
            }
        )
    except Exception as e:
        return f"Error storing order: {str(e)}"
    
    return f"Order has been placed successfully! Order ID: {str(order_id)}, Tracking ID: {tracking_id}. Product IDs are {product_ids_str}"