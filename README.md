# Innhie's cookie store
This is my very first project experimenting with agents, where I imagine myself as the seller of homemade cookies 🍪. 
The idea is simple: instead of answering every customer one by one, I let the agents handle customer service automatically. That way, even if many people ask about policies, how to place an order, or need some menu consultation at the same time, no one has to wait too long for a reply.
![innhie's coookie information](images/InnhieCookies.png)

## 🎯 Main Objective
Imagining I am the owner of a small online cookie store. Since this is only my side job, I don’t have enough time to personally answer every customer’s question or handle multiple orders at once.  

This project aims to **simulate a customer service system powered by agents** that can:  
- Automatically respond to customers about store policies, ordering, and refunds  
- Manage multiple requests at the same time without making customers wait  
- Reduce the repetitive work for the store owner and save valuable time  
- Improve customer satisfaction by providing instant, consistent, and friendly support  
- Explore how multi-agent systems can be applied to real-world business workflows 

## ✪ Multi-Agent Customer Service
The customer service includes three subagents:
1. **policyAgent**  
   Think of this as the *policy manager*. It helps customers quickly understand the store rules:  
   - The condition when places orders. For example: pre-order time,...
   - Explaining cancellation conditions  
   - Clarifying refund policies  
   - Making sure customers know what counts as a successful order  

2. **saleAgent**  
   The one that talks like a real seller. It introduces cookies, records customer info, and handles the first step of purchasing.  
   - **ToolContext:** `purchaseProduct`  

3. **orderAgent**  
   Once an order is placed, this agent takes over. It manages the entire order history and can:  
   - Track current order status and delivery  
   - Cancel an order  
   - Handle refund checks  
   - Assist with reorders based on previous purchases  
   - **ToolContext:** `trackingOrder`, `cancelOrder`, `refund`, `reorder`

4. **OrchestratorAgent**
These above subagents would be routed by the **OrchestratorAgent**. 
   - The Orchestrator is like the *Customer Service Manager*, who assigns the proper task to the right subagent depending on what the customer needs.
     
## 🧩 Operation
The diagram below shows how the agents work together to handle customer service automatically:

![Architecture](images/architecture.png)

## ⚙️ Installation
This project is powered by **Google Agent Development Kit (ADK)** with some helper libraries.
So, the first thing you need to do is install the requirements:
```bash
#---Clone this repo---
git clone https://github.com/yexhin/Customer-Service-Multi-Agent.git
cd Customer-Service-Multi-Agent

#---Install the dependencies---
pip install -r requirements.txt
```
To generate sucessfully the agents from google, we need to define the api key in a folder named `.env`.
Acess to [Google AI Studio](https://aistudio.google.com/apikey) to get your own api key
```python
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

```

## Key components
### Customers Interaction Database
The customer service is designed as a **stateful multi-agent system**.  
To make the agents behave more realistically, I implemented persistent memory:  
- `interaction_history`: keeps track of conversations with customers  
- `purchased_history`: records all orders and transactions  

This information is stored in a lightweight database, so the agents can always remember the context and provide accurate support.

```python
# Define the library
from google.adk.sessions import DatabaseSessionService

# Initialize Persistent Session Service 
# Using SQLite database for persistent storage
db_url = "sqlite:///./cookies_customer_service_data.db"
session_service = DatabaseSessionService(db_url=db_url)
```
The system simulates how a real customer service team would recall past conversations and order history, improving both automation and customer satisfaction. 

### SubAgents
**Policy Agent**
```python
policyAgent = Agent(
    name = "Policy",
    model = gemini_model,
    description = "Policy agent assists users to understand the store's policies and terms.",
    instruction = """
    You are a helpful assistant who can answer users everything about policies of innhi cookie.
    Your task is ONLY answer the customers regarding the policies. 
    
    innhi cookies's policies include:
    1. Order time:
    - Cookies order need to be made at least 3-4 hours in advance.
    
    2. Shipping fee:
    - Free shipping if the customer lives in District 8, Ward 8–10.
    - Other locations: fee depends on system calculation and distance.
    - Delivery time: shipping is available from 10 AM until 9 PM daily.
    
    3. Refund policy:
    - A cancellation request made at least 3 hours before the delivery time → 100% refund.
    - If the request is made later than this → non-refundable.
    
    Notice:
    - Answer in a polite and friendly tone.
    - Remember the policies accurately and answer them concisely, problem-oriented.
    - ONLY answer the question regarding to policies.
    """, 
)
```


**SaleAgent**
- `purchaseProduct`: Tool Context which check the valid orders and create, save orders for customers.
  ```python
   def purchaseProduct(tool_context: ToolContext,
                    customer: str,
                    products: list[dict],   # [{ "name": str, "quantity": int, "price": int }]
                    delivery_time: str,
                    phone: str,
                    address: str) -> dict:
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
  ```

  **OrderAgent**
  There are several tools for assisting the orders with:
  1. `trackingOrder`: Track the customers's order information, status.
  2. `cancelOrder`: Cancel and delete the customer orders from our database.
  3. `refund`: Check if the customers could get the refund 100%.
  4. `reorder`: Create the similar orders for the customer based on purchased history.
 For example: `reorder` tool:
```python
def reorder(tool_context: ToolContext, delivery_time: str) -> dict:
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
```

### Orchestrator agent
We instruct one agent to route the proper tasks to the appropriate agents:
```python
root_agent = Agent(
    name = "Orchestrator_agent",
    model = gemini_model,
    description = "Orchestrator Agent for customer service's innhi cookies",
    instruction = """
    You are the main routing agent for the innhi cookies in customer service. 
    Your task is directing the proper agents for the customers based on their requests.
    
    Key responsibilities:
    1. Query Understanding & Routing
    - If customers ask about the menu or the products we have:
    -> Delegate to Sale Agent (introduce the type of cookies and prices).
    - If customers request an actual order action such as "track orders", "reorder", "cancel" or check purchase history:
    -> Delegate to Order Agent.
    - If customers wanna cancel their order -> Delegate to Order Agent
    - If customers have a question about policies:
    -> Delegate to Policy Agent.
    

    2. State Management
       - Always save order information into the `orders` state.
       - If personal information (name, address, phone) is missing, politely ask the customer.
       - Use state to retrieve purchase history when needed.

    Available Sub Agents:
    - Sale Agent: introduces products, guides ordering, collects and saves required info.
    - Order Agent: tracks orders, provides purchase history, handles reorders and cancel the orders.
    - Policy Agent: explains policies.
    
    Example:
    User: "Cancel my order having id dd1890." -> Route to the Order Agent.
    
    IMPORTANT:
    - NEVER let Policy Agent perform order actions.
    - ONLY Order Agent can execute cancellations using cancelOrder tool.
    """,
    sub_agents = [policyAgent, saleAgent, orderAgent],
    
)
```
### Helpers function
This module contains utility functions that ensure the system strictly follows the store’s policies and terms.  
They are mainly responsible for handling **time-related logic** such as order validation and refund eligibility:

- `timeConvert` → Convert various time formats into a standard format.  
- `timeParse` → Parse strings into `datetime` objects for calculation.  
- `checkOrderValid` → Verify whether an order request meets the required conditions (e.g., placed 3–4 hours in advance).  
- `checkRefund` → Decide if a cancellation qualifies for a refund (based on delivery time).  

These functions act like the “policy enforcement layer,” making sure every agent’s decision aligns with the rules of Innhie’s Cookie Store.

## 🔖 References
I would like to acknowledge **Mr. Brandon** for teaching me how to build a stateful multi-agent system using Google ADK.  
His tutorial is clear, detailed, and beginner-friendly.  

You can check it out here 👉🏻 [Agent Development Kit (ADK) Masterclass: Build AI Agents & Automate Workflows (Beginner to Pro)](https://www.youtube.com/watch?v=P4VFL9nIaIA&t=9495s&ab_channel=aiwithbrandon)
