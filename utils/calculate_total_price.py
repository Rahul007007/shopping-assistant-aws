from typing import List

def checkout(product_id: str, quantity: str, product_price: float, discount: float):
    """Returns the total price associated with each product_id after multiplying the quantity with the product_price and considering the discount as well.
    """
    try:
        quantity = int(quantity)
        if quantity < 0:
            raise ValueError("Quantity must be a non-negative integer.")
    except ValueError:
        raise ValueError("Quantity must be a valid integer.")

    if product_price < 0 or discount < 0:
        raise ValueError("Product price and discount must be non-negative.")

    total_price = quantity * product_price
    discounted_price = total_price - discount

    return round(discounted_price, 2)

def calculate_total_price(cart_items:List, shipment_distance: float):
    """Calculates the total price of the items in the cart before final payment by considering the product_price along with the quanity and discount and the total shipment cost.
    """
    total_price = 0
    product_ids_str = ""
    for item in cart_items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        product_price = item.get('product_price')
        discount = item.get('discount')
        total_price += checkout(product_id, quantity, product_price, discount)
        product_ids_str+=str(item['product_id'])+" "
    total_price += shipment_distance * 0.1
    return f"Total price to be paid for the cart items consisting of Product IDs: {product_ids_str} after considering the delivery charges and the product prices with their discounts: {total_price}"