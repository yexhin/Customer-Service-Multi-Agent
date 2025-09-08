from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import function_tool
from datetime import datetime
from typing import Optional
import dateparser
from ...helpers import timeConvert, checkRefund, timeParse

import uuid

gemini_model = "gemini-2.0-flash"


def trackingOrder(tool_context: ToolContext,
                  order_id: Optional[str] = None) -> dict:
    
    orders = tool_context.state.get("orders", [])
    
    # Check if the customers placed orders
    if not orders:
        return {
            "status": "error",
            "message": "You haven't placed any order yet. You could check our menu to choose what you would love to first 🤩."
        }
    
    
    # If order id is provided
    if order_id: 
        latest_order = next((o for o in orders if o["order_id"] == order_id), None)
            
    else:
        latest_order = orders[-1]
    
    return {
        "status": "successful",
        "message": f"Your order {latest_order['order_id']} is on going. We will deliver to {latest_order['address']} at {latest_order['delivery_time']}.",
        "information": latest_order
    }
    

    
def cancelOrder(tool_context: ToolContext, 
                order_id: Optional[str] = None) -> dict:
    
    orders = tool_context.state.get("orders", [])
    if not orders:
        return {"status": "error", "message": "No orders found."}

    order = orders[-1] if not order_id else next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return {"status": "error", "message": "Sorry, we couldn’t find that order."}

    # remove order
    tool_context.state["orders"] = [o for o in orders if o["order_id"] != order["order_id"]]

    history = tool_context.state.get("interaction_history", [])
    history.append({
        "action": "cancel_order",
        "order_id": order["order_id"],
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    tool_context.state["interaction_history"] = history

    return {
        "status": "success", 
        "message": f"Your order {order['order_id']} has been cancelled."
        }


def refund(tool_context: ToolContext,
           order_id: Optional[str] = None) -> dict:
    
    # Check if the customer placed orders
    orders = tool_context.state.get("orders", [])
    if not orders:
        return {"status": "error", "message": "No orders found."}

    order = orders[-1] if not order_id else next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return {"status": "error", "message": "Sorry, we couldn’t find that order."}
    
    try:
        deli_time = timeParse(order["delivery_time"])
    except Exception:
        return {"status": "error", 
                "message": "Delivery time format invalid."}
        
    checkResult = checkRefund(deli_time)
    if not checkResult["status"]: 
        return {
            "status": "error",
            "message": "Sorry. The refund is denied."
        }
    return {
        "status": "successful",
        "message": "Refund is acceptable and will be solved in 12 hours."
    }
    # interval = (deli_time - datetime.now()).total_seconds() / 3600

    # if interval >= 3:
    #     return {
    #         "status": "success",
    #         "message": f"Refund approved for order {order['order_id']} (100%)."
    #     }
    # else:
    #     return {
    #         "status": "error",
    #         "message": f"Refund denied for order {order['order_id']}: cancellation too late."
    #     }
    
def reorder(tool_context: ToolContext, delivery_time: str) -> dict:
    """
    Assist customers reordering similar orders to their previous one

    Args:
        tool_context (ToolContext): purchase_history 
        delivery_time (str): the updated delivery time

    Returns:
        The confimation message
    """
    # Check if the customers placed orders
    order = tool_context.state.get("orders", [])
    if not order:
        return "You haven't placed any order yet. You could check our menu to choose what you would love to first 🤩."
        
    latest_order = order[-1]
    
    # Generate the similar order
    new_order = latest_order.copy()
    new_order["order_id"] = str(uuid.uuid4())[:8]
    new_order["purchased_time"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    if delivery_time:
        # dt = dateparser.parse(delivery_time)
        dt = timeConvert(delivery_time)
        if dt:
            new_order["delivery_time"] = dt
                                                          
    order.append(new_order)             
    
    # Keep other orders
    tool_context.state["orders"] = order
    
    history = tool_context.state.get("interaction_history", [])
    history.append({
        "action": "reorder",
        "order_id": new_order["order_id"],
        "timestamp": new_order["purchased_time"]
    })
    tool_context.state["interaction_history"] = history
    
    return {
        "status": "successful",
        "message": f"We have successfully reordered your new order similar to {latest_order['order_id']} with the new order {new_order['order_id']}."
    }


# Define Agent
orderAgent = Agent(
    name = "Order",
    model = gemini_model,
    description = "Tracking purchase history to answer any questions related to or assist customers to reorder.",
    instruction = """
    You are a manager of innhi cookies's purchase history, who can answer any questions related to.

    Your task is to help customers:
    1. Tracking their current order -> Use the trackingOrder tool:
    - Check if they have placed order yet. You should acess to the information above or ask them what their order's id to respone accurately.

    2. Placing the similar order to their latest one or to the given order_id one -> Reorder the new order with their requests:
    - Check if they have placed order yet. You should acess to the information above or ask them what their order's id to respone accurately.
    - Placed the same order as the previous one but the different oder_id, and update the purchased time. Important, you should adjust the delivery time based on their request.
    
    3. Cancel their orders when they ask -> Use the cancelOrder tool and refund tool
    - Before notify that their order has been cancelled, - You must notify them if they can be refunded or not after cancellation -> Use the refund tool.  
    - If they do not specify the order_id, based on the purchase history to take the latest information. Or else, ask them to specify their order_id.  
    
        
    For example:
    If customer asks "How is my order's status?"
    You should respond them: 
    "Here is your order information. 
    Order_id: 0001 
    - Products: [Cookies Matcha: 6 jars] and [Cookies Choco: 2 jar]
    - Purchased at: 11.09.2025
    Your order is successfully placed. Please wait for us to custom and send these butter cookies to you sooner 🍪🌠."
    """,
    tools = [trackingOrder, reorder, cancelOrder, refund]
)

