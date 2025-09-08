import asyncio
from dotenv import load_dotenv
import os
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from agent.agent import root_agent
from utils import call_agent_async, add_agent_response_to_history, add_user_query_to_history

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Persistent Session Service 
# Using SQLite database for persistent storage
db_url = "sqlite:///./cookies_customer_service_data.db"
session_service = DatabaseSessionService(db_url=db_url)

# Define Initial State
# This will only be used when creating a new session
initial_state = {
    "user_name": "Be Nhi",
    "orders": [],
    "interaction_history": [],
}

async def main_async():
    # Set up constant
    APP_NAME = "Customer_Service_Agent"
    USER_ID = "BeNhiLiuGrace"
    
    # Session Management
    # Check for existing sessions
    existing_session = await session_service.list_sessions(
        app_name= APP_NAME,
        user_id = USER_ID,
    )
    
    # If there's an existing session, use it, otherwise create a new one
    if existing_session and len(existing_session.sessions) > 0:
        # Use the most recent session
        SESSION_ID = existing_session.sessions[0].id
        print(f"Continuing existing session: {SESSION_ID}")
    else:
        # Create a new sessiom with initial state
        new_session = await session_service.create_session(
                app_name = APP_NAME,
                user_id = USER_ID,
                state = initial_state,
                )
    
        SESSION_ID = new_session.id
        print(f"Created new session: {SESSION_ID}")
        
    # Create runner
    runner = Runner(
            app_name = APP_NAME,
            agent = root_agent,
            session_service = session_service, 
    )
        
    print("Warm welcome to our beloved customers, what cookies you would like to bring home today?")
    print("º∙👩🏻₊˚🍪 ˚ෆ")
        
    while True:
        # Customer 
        user_input = input("You: ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for choosing us today! We are looking forward to our next cookies 🤎.")
            break
        
        # Clear session
        if user_input.lower() in ["clear", "delete session"]:
            await session_service.delete_session(
                app_name = APP_NAME,
                user_id = USER_ID,
                session_id = SESSION_ID,
            )
            
            print("Session deleted.")

            # Generate new session with initial state
            new_session = await session_service.create_session(
                app_name=APP_NAME,
                user_id=USER_ID,
                state=initial_state,
            )
            SESSION_ID = new_session.id
            print(f"Created new session: {SESSION_ID}")
            continue
        
            
        # Update interaction history with the user's query
        await add_user_query_to_history(
            session_service, APP_NAME, USER_ID, SESSION_ID, user_input
        )

        # Process the user query through the agent
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)
            
if __name__ == "__main__":
    asyncio.run(main_async())