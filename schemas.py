from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class Get_Product_Recommendations(BaseModel):
    query_text: str = Field(..., title="query_text", description="The query text for which the product recommendations are requested")
    model_config = ConfigDict(extra="forbid")

class Add_To_Cart(BaseModel):
    product_id: int = Field(..., title="product_id", description="The unique Product ID of the product to purchase")
    quantity: int = Field(..., title="quantity", description="The number of items to purchase")
    model_config = ConfigDict(extra="forbid")

class Shipment_Details(BaseModel):
    destination: str = Field(..., title="destination", description="The destination where the order has to be shipped to.")
    model_config = ConfigDict(extra="forbid")

class CartItem(BaseModel):
    product_id: int = Field(..., description="Unique identifier for the product")
    quantity: int = Field(..., description="Number of items purchased")
    product_price: float = Field(..., description="Price per unit of the product")
    discount: Optional[float] = Field(..., description="Discount on the product")

class Calculate_Total_Price(BaseModel):
    cart_items: List[CartItem] = Field(..., description="List of items in the cart")
    shipment_distance: float = Field(..., description="Distance for shipment")
    model_config = ConfigDict(extra="forbid")
    
class Complete_Purchase(BaseModel):
    total_price: float = Field(..., description="Total cost of the order")
    cart_items: List[CartItem] = Field(..., description="List of items in the cart")

class Get_Order_Details(BaseModel):
    order_id: int = Field(...,  title="order_id", description="Unique identifier for the order")
    model_config = ConfigDict(extra="forbid")

