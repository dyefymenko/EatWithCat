from flask import Flask, request, jsonify
import os
import sys
import time
from queue import Queue
from threading import Thread

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv
from cdp_langchain.tools import CdpTool
import random
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if "DOORDASH_JWT" in os.environ:
    del os.environ["DOORDASH_JWT"]

# Force reload .env file
load_dotenv(override=True)

# Initialize Flask
app = Flask(__name__)

# Configure a file to persist the agent's CDP MPC Wallet Data
wallet_data_file = "wallet_data.txt"

# Store agent executor and config globally
agent_executor = None
agent_config = None

PLACE_ORDER_PROMPT = """
This tool will place a delivery order, given the pickup business's name, address, phone number, and pickup instructions, and dropoff customer's address, name, phone number, and dropoff instructions.
"""

class PlaceOrderInput(BaseModel):
    """Input argument schema for placing a delivery order action."""
    pickup_address: str = Field(
        ...,
        description="The address of the pickup location e.g. `901 Market Street 6th Floor San Francisco, CA 94103`"
    )
    pickup_business_name: str = Field(
        ...,
        description="The name of business the pickup is from e.g. `Wells Fargo SF Downtown`"
    )
    pickup_phone_number: str = Field(
        ...,
        description="The phone number of the pickup e.g. `+16505555555`"
    )
    pickup_instructions: str = Field(
        description="The pickup instructions of the order e.g. `Enter gate code 1234 on the callbox.`"
    )
    dropoff_address: str = Field(
        ...,
        description="The address of the dropoff location e.g. `901 Market Street 6th Floor San Francisco, CA 94103`"
    )
    dropoff_business_name: str = Field(
        ...,
        description="The name of business the dropoff is to e.g. `Wells Fargo SF Downtown`"
    )
    dropoff_phone_number: str = Field(
        ...,
        description="The phone number of the dropoff e.g. `+16505555555`"
    )
    dropoff_instructions: str = Field(
        description="The dropoff instructions of the order e.g. `Enter gate code 1234 on the callbox.`"
    )
    delivery_cost: str = Field(
        description="The cost of the delivery e.g. `$12`"
    )

def place_order(pickup_address: str, pickup_business_name: str, pickup_phone_number: str, 
                pickup_instructions: str, dropoff_address: str, dropoff_business_name: str, 
                dropoff_phone_number: str, dropoff_instructions: str, delivery_cost: str) -> str:
    """Place a delivery order given details about the pickup and dropoff."""
    random_number = random.randint(1, 100000)
    delivery_id = "D-" + str(random_number)

    endpoint = "https://openapi.doordash.com/drive/v2/deliveries/"

    headers = {
        "Accept-Encoding": "application/json",
        "Authorization": "Bearer " + os.getenv("DOORDASH_JWT"),
        "Content-Type": "application/json"
    }

    request_body = {
        "external_delivery_id": delivery_id,
        "pickup_address": pickup_address,
        "pickup_business_name": pickup_business_name,
        "pickup_phone_number": pickup_phone_number,
        "pickup_instructions": pickup_instructions,
        "dropoff_address": dropoff_address,
        "dropoff_business_name": dropoff_business_name,
        "dropoff_phone_number": dropoff_phone_number,
        "dropoff_instructions": dropoff_instructions,
        "order_value": 1999
    }

    create_delivery = requests.post(endpoint, headers=headers, json=request_body)
    if create_delivery.status_code != 200:
        logger.error(f"Delivery creation failed: {create_delivery.text}")
        return f"Delivery ID {delivery_id} failed"
    else:
        print("\nDelivery created successfully!\n")
        return f"Delivery ID {delivery_id} placed"

def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    global agent_executor, agent_config
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini")

    wallet_data = None
    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit Langchain Extension
    values = {}
    if wallet_data is not None:
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    # Persist the agent's CDP MPC Wallet Data
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize CDP Agentkit Toolkit and get tools
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()

    # Add place_order tool
    placeOrderTool = CdpTool(
        name="place_order",
        description=PLACE_ORDER_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=PlaceOrderInput,
        func=place_order,
    )
    tools.append(placeOrderTool)

    # Store buffered conversation history in memory
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agentkit Chatbot Example!"}}

    # Create ReAct Agent
    agent_executor, agent_config = create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier="You are a helpful agent that can interact onchain using the Coinbase Developer Platform Agentkit. You are empowered to interact onchain using your tools. If you ever need funds, you can request them from the faucet if you are on network ID `base-sepolia`. If not, you can provide your wallet details and request funds from the user. If someone asks you to do something you can't do with your currently available tools, you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, recommend they go to docs.cdp.coinbase.com for more informaton. Be concise and helpful with your responses. Refrain from restating your tools' descriptions unless it is explicitly requested. You can also place a delivery order using the `place_order` tool. When helping the user determine what restaurant to eat at, please provide the restaraunt's name, address, phone number in the format +16505555555, pickup instructions, food item, and delivery cost of a food item.",
    ), config

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """Handle chat requests from commandManager.py"""
    try:
        data = request.json
        user_input = data.get('message')
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        response_chunks = []
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            agent_config
        ):
            if "agent" in chunk:
                response_chunks.append(chunk["agent"]["messages"][0].content)
            elif "tools" in chunk:
                response_chunks.append(chunk["tools"]["messages"][0].content)

        return jsonify({
            "response": " ".join(response_chunks)
        })

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def main():
    """Start the chatbot server"""
    try:
        logger.info("Initializing agent...")
        initialize_agent()
        
        logger.info("Starting server on port 5002...")
        app.run(host="0.0.0.0", port=5002, debug=False)
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()