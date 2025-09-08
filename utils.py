from datetime import datetime
from google.genai import types


async def update_interaction_history(session_service, app_name, user_id, session_id, entry):
    """Add an entry to the interaction history in state.

    Args:
        session_service: The session service instance
        app_name: The application name
        user_id: The user ID
        session_id: The session ID
        entry: A dictionary containing the interaction data
            - requires 'action' key (e.g., 'user_query', 'agent_response')
            - other keys are flexible depending on the action type
    """
    
    try: 
        # Get current session
        session = await session_service.get_session(
                app_name = app_name,
                user_id = user_id,
                session_id = session_id
            )
            
        # Get current history
        interaction_history = session.state.get("interaction_history", [])
            
        # Add timestamp if not in the entry
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                
        # Add entry into the interaction_history
        interaction_history.append(entry)
            
        
        # Create updated state
        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        # Create a new session with updated state
        session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state,
        )
        
    except Exception as e:
        print(f"Error updating interaction history: {e}")
        
        
        

async def add_user_query_to_history(session_service, 
                              app_name, 
                              user_id, 
                              session_id, 
                              query):
    """Add a user query to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query,
        },
    )


async def add_agent_response_to_history(session_service, 
                                  app_name, 
                                  user_id, 
                                  session_id, 
                                  agent_name, 
                                  response):
    """Add an agent response to the interaction history."""
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response,
        },
    )


async def display_state(session_service, 
                        app_name,
                        user_id,
                        session_id,
                        label = "Current state"):
    try:
        session = await session_service.get_session(
            app_name = app_name,
            user_id = user_id,
            session_id = session_id
        )
        
        print(f"\n{'-' * 10} {label} {'-' * 10}")
        
        # Handle the user name
        user_name = session.state.get("user_name", "Unknown")
        
        print(f"👤 User: {user_name}")
        
        # Handle orders info
        orders = session.state.get("orders", [])
        if orders or any(orders):
            print("Recepit:")
            for i, order in enumerate(orders, 1):
                print(f"\n=== Order {i} ===")
                print(f"Order ID: {order.get('order_id')}")
                print(f"Customer: {order.get('customer_name')}")
                print(f"Address: {order.get('address')}")
                print(f"Phone: {order.get('phone')}")
                print(f"Delivery Time: {order.get('delivery_time')}")
                print(f"Purchased Time: {order.get('purchased_time')}")

                # Loop products
                print("\nProducts:")
                products = order.get("products", [])
                for j, product in enumerate(products, 1):
                    print(f"  {j}. {product.get('name', 'N/A')} "
                        f"x{product.get('quantity', 1)} "
                        f"- {product.get('price', 0)}")

                # Show total
                print(f"\nSubtotal (no shipping): {order.get('temp_total_not_include_shipping_fee', 0)}")
                print("=" * 30)

        else:
            print("There is none.")
            
    except Exception as e:
        print(f"Error display state: {e}")
        
        
async def process_agent_response(event):
    # Log basic event info
    print(f"Event ID: {event.id}, Author: {event.author}")

    # Check for specif ic parts first
    has_specific_part = False
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "executable_code") and part.executable_code:
                # Access the actual code string via .code
                print(
                    f"  Debug: Agent generated code:\n```python\n{part.executable_code.code}\n```"
                )
                has_specific_part = True
            elif hasattr(part, "code_execution_result") and part.code_execution_result:
                # Access outcome and output correctly
                print(
                    f"  Debug: Code Execution Result: {part.code_execution_result.outcome} - Output:\n{part.code_execution_result.output}"
                )
                has_specific_part = True
            elif hasattr(part, "tool_response") and part.tool_response:
                # Print tool response information
                print(f"  Tool Response: {part.tool_response.output}")
                has_specific_part = True
            # Also print any text parts found in any event for debugging
            elif hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    # Check for final response after specific parts
    final_response = None
    if event.is_final_response():
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text.strip()
            print(
                f"\n╔══ AGENT RESPONSE ═════════════════════════════════════════"
            )
            print(f"{final_response}")
            print(
                f"╚═════════════════════════════════════════════════════════════\n"
            )
        else:
            print(
                f"\n==> Final Agent Response: [No text content in final event]\n"
            )

    return final_response


async def call_agent_async(runner, user_id, session_id, query):
    """Call the agent asynchronously with the user's query."""
    
    content = types.Content(
        role="user", 
        parts=[types.Part(text=query)]
        )
    
    print(
        f"\n--- Running Query: {query} ---"
    )
    final_response_text = None
    agent_name = None

    # Display state before processing
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State BEFORE processing",
    )

    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            # Capture the agent name from the event if available
            if event.author:
                agent_name = event.author

            # Process each event and get the final response if available
            response = await process_agent_response(event)
            if response:
                final_response_text = response
    except Exception as e:
        print(f"Error during agent call: {e}")
        
        
     # Add the agent response to interaction history if we got a final response
    if final_response_text and agent_name:
        await add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text,
        )


    # Display state after processing the message
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State AFTER processing",
    )

    return final_response_text