import random

def complete_purchase(total_price: float, cart_items: list):
    """Generates a short order ID and tracking ID, then confirms order placement."""
    order_id = str(random.randint(1000, 9999))
    tracking_id = str(random.randint(100000, 999999))
    product_ids_str =""
    for cart_item in cart_items:
        product_ids_str+=str(cart_item['product_id'])+" "
    return f"Order has been placed successfully! Order ID: {order_id}, Tracking ID: {tracking_id}. Product IDs are {product_ids_str}"