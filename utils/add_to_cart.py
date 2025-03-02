import random

def add_to_cart(product_id: int, quantity: int) -> str:
    """
    Used to add a product to the cart given the product_id and quantity, so that the items can be checked out.
    """

    return f"Order with product_id: {product_id} of quantity: {quantity} has been added to the cart ✅"

if __name__ == "__main__":
    print(add_to_cart(886368088, 2))