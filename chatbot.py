import os
import sys
import time

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# Import CDP Agentkit Langchain Extension.
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

# Adding more functionalities to Agent
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv
from cdp_langchain.tools import CdpTool

# Load the .env file
load_dotenv()


# TODO: add "check delivery status" action

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
    ) # optional i think?
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
    ) # optional i think?
    delivery_cost: str = Field(
        description="The cost of the delivery e.g. `$12`"
    ) 

def place_order(pickup_address: str, pickup_business_name: str, pickup_phone_number: str, pickup_instructions: str, dropoff_address: str, dropoff_business_name: str, dropoff_phone_number: str, dropoff_instructions: str, delivery_cost: str) -> str:
    """Place a delivery order given details about the pickup and dropoff.

    Args:
        wallet (Wallet): The wallet to sign the message from.
        message (str): The message to hash and sign.

    Returns:
        str: The delivery ID.

    """
    #tx = wallet.transfer(hash_message(message)).wait()
    delivery_id = "D-12345"

    endpoint = "https://openapi.doordash.com/drive/v2/deliveries/"

    headers = {"Accept-Encoding": "application/json",
            "Authorization": "Bearer " + os.getenv("DOORDASH_JWT"),
            "Content-Type": "application/json"}

    request_body = { # Modify pickup and drop off addresses below
        "external_delivery_id": delivery_id,
        "pickup_address": pickup_address,
        "pickup_business_name": pickup_business_name,
        "pickup_phone_number": pickup_phone_number,
        "pickup_instructions": pickup_instructions,
        "dropoff_address": dropoff_address,
        "dropoff_business_name": dropoff_business_name,
        "dropoff_phone_number": dropoff_phone_number,
        "dropoff_instructions": dropoff_instructions,
        "order_value": 1999 # TODO: determine what this is
    }

    create_delivery = requests.post(endpoint, headers=headers, json=request_body) # Create POST request


    return f"Delivery ID {delivery_id} placed"

# Configure a file to persist the agent's CDP MPC Wallet Data.
wallet_data_file = "wallet_data.txt"


def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    # Initialize LLM.
    llm = ChatOpenAI(model="gpt-4o-mini")

    wallet_data = None

    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    # Configure CDP Agentkit Langchain Extension.
    values = {}
    if wallet_data is not None:
        # If there is a persisted agentic wallet, load it and pass to the CDP Agentkit Wrapper.
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    # persist the agent's CDP MPC Wallet Data.
    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    # Initialize CDP Agentkit Toolkit and get tools.
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()

    # Define a new tool for signing messages.
    placeOrderTool = CdpTool(
    name="sign_message",
    description=PLACE_ORDER_PROMPT,
    cdp_agentkit_wrapper=agentkit,
    args_schema=PlaceOrderInput,
    func=place_order,
    )

    all_tools = tools.append(placeOrderTool)

    # Store buffered conversation history in memory.
    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agentkit Chatbot Example!"}}

    # Create ReAct Agent using the LLM and CDP Agentkit tools.
    return create_react_agent(
        llm,
        tools=all_tools,
        checkpointer=memory,
        state_modifier="You are a helpful agent that can interact onchain using the Coinbase Developer Platform Agentkit. You are empowered to interact onchain using your tools. If you ever need funds, you can request them from the faucet if you are on network ID `base-sepolia`. If not, you can provide your wallet details and request funds from the user. If someone asks you to do something you can't do with your currently available tools, you must say so, and encourage them to implement it themselves using the CDP SDK + Agentkit, recommend they go to docs.cdp.coinbase.com for more informaton. Be concise and helpful with your responses. Refrain from restating your tools' descriptions unless it is explicitly requested. You can also place a delivery order using the `place_order` tool. When helping the user determine what restaurant to eat at, please provide the restaraunt's name, address, phone number, pickup instructions, food item, and price of food item.",
    ), config


# Autonomous Mode
def run_autonomous_mode(agent_executor, config, interval=10):
    """Run the agent autonomously with specified intervals."""
    print("Starting autonomous mode...")
    while True:
        try:
            # Provide instructions autonomously
            thought = (
                "Be creative and do something interesting on the blockchain. "
                "Choose an action or set of actions and execute it that highlights your abilities."
            )

            # Run agent in autonomous mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=thought)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

            # Wait before the next action
            time.sleep(interval)

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Chat Mode
def run_chat_mode(agent_executor, config):
    """Run the agent interactively based on user input."""
    print("Starting chat mode... Type 'exit' to end.")
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() == "exit":
                break

            # Run agent with the user's input in chat mode
            for chunk in agent_executor.stream(
                {"messages": [HumanMessage(content=user_input)]}, config
            ):
                if "agent" in chunk:
                    print(chunk["agent"]["messages"][0].content)
                elif "tools" in chunk:
                    print(chunk["tools"]["messages"][0].content)
                print("-------------------")

        except KeyboardInterrupt:
            print("Goodbye Agent!")
            sys.exit(0)


# Mode Selection
def choose_mode():
    """Choose whether to run in autonomous or chat mode based on user input."""
    while True:
        print("\nAvailable modes:")
        print("1. chat    - Interactive chat mode")
        print("2. auto    - Autonomous action mode")

        choice = input("\nChoose a mode (enter number or name): ").lower().strip()
        if choice in ["1", "chat"]:
            return "chat"
        elif choice in ["2", "auto"]:
            return "auto"
        print("Invalid choice. Please try again.")


def main():
    """Start the chatbot agent."""
    agent_executor, config = initialize_agent()

    mode = choose_mode()
    if mode == "chat":
        run_chat_mode(agent_executor=agent_executor, config=config)
    elif mode == "auto":
        run_autonomous_mode(agent_executor=agent_executor, config=config)


if __name__ == "__main__":
    print("Starting Agent...")
    main()