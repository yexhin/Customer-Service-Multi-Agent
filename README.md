# Innhie's cookie store
This is my very first project experimenting with agents, where I imagine myself as the seller of homemade cookies 🍪. The idea is simple: instead of answering every customer one by one, I let the agents handle customer service automatically. That way, even if many people ask about policies, how to place an order, or need some menu consultation at the same time, no one has to wait too long for a reply.
![innhie's coookie information](images/InnhieCookies.png)

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

4. **orchestorAgent**
These above subagents would be routed by the **orchestorAgent**. 
   - The Orchestrator is like the *Customer Service Manager*, who assigns the proper task to the right subagent depending on what the customer needs.
     
## 🧩 Operation
The diagram below shows how the agents work together to handle customer service automatically:

![Architecture](images/architecture.png)

## ⚙️ Installation
This project is powered by **Google Agent Development Kit (ADK)** with some helper libraries.
So, the first thing you need to do is install the requirements:
```bash
---Clone this repo---
git clone https://github.com/yexhin/Customer-Service-Multi-Agent.git
cd Customer-Service-Multi-Agent

---Install the dependencies---
pip install -r requiremnets.txt
```



