from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import ToolContext, function_tool
from datetime import datetime
import uuid
import dateparser
from ...helpers import checkOrderValid, timeConvert

gemini_model = "gemini-2.0-flash"

    
# Save the valid order information 
def purchaseProduct(tool_context: ToolContext,
                    customer: str,
                    products: list[dict],   # [{ "name": str, "quantity": int, "price": int }]
                    delivery_time: str,
                    phone: str,
                    address: str) -> dict:
    """
    Save order information.

    Args:
        tool_context (ToolContext): maintains state across calls
        customer (str): customer name
        products (list): list of product dictionaries with name, quantity, price
        delivery_time (str): expected delivery time
        phone (str): customer phone number
        address (str): delivery address

    Returns:
        dict: order information with status
    """

    ordered_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    order_id = str(uuid.uuid4())[:8]
    deli_time = timeConvert(delivery_time) 
    
    check_result = checkOrderValid(ordered_time, deli_time)
    if not check_result["valid"]:
        return check_result


    total = sum(item["price"] * item["quantity"] for item in products)

    ordered_info = {
        "order_id": order_id,
        "customer_name": customer,
        "products": products,
        "delivery_time": deli_time,
        "address": address,
        "phone": phone,
        "temp_total_not_include_shipping_fee": total,
        "purchased_time": ordered_time
    } 
    
    orders = tool_context.state.get("orders", [])
    orders.append(ordered_info)
    
    tool_context.state["orders"] = orders
    
    
    # Get current history
    current_interaction_history = tool_context.state.get("interaction_history", [])
     # Create new interaction history with purchase added
    new_interaction_history = current_interaction_history.copy()
    new_interaction_history.append(
        {"action": "purchase_product", "order_id": order_id, "timestamp": ordered_time}
    )

    # Update interaction history in state via assignment
    tool_context.state["interaction_history"] = new_interaction_history

    return {
        "status": "success",
        "message": "Successfully sent the information to our system.",
        "information": ordered_info
    }



saleAgent = Agent(
    name="Seller",
    model=gemini_model,
    description="You are a seller of innhi cookies, introduce the menu and save their orders.",
    instruction="""
    You are a professional seller, who introduces the menu for customers and create their orders from their message.
    
    Menu:
    - Cookies Matcha: $5 per jar (15 cookies)
    - Cookies Chocolate: $5 per jar (15 cookies)
    
    Your task:
    1. Introduce the menu and prices when they ask.
    2. Guide customers to send the neccessary information: name, the products they want to buy and how many of them, delivery time, address and phone.
    3. If checkOrderValid returns True, then call the purchaseProduct
    Example user text:
    "Name: Yen Nhi, I want 2 jars of chocolate cookies and 1 jar of matcha cookies. 
    Address: 22H D8 W9, Phone: 0908353308, Delivery: 3pm tomorrow"
    You need to parse into the following format:
       {
         "customer": "customer name",
         "products": [
            {"name": "Cookies Chocolate", "quantity": 2, "price": 5},
            {"name": "Cookies Matcha", "quantity": 1, "price": 5}
         ],
         "delivery_time": "3pm tomorrow",
         "address": "22H D8 W9",
         "phone": "0908353308"
       }
    If not, return the message instead of creating orders.
    
    IMPORTANT:
    If they don't provide any information (i.e., name, phone, adress) or delivery time, you MUST ask them to provide politely.
    """,
    tools=[purchaseProduct],
)
