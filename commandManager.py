from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import asyncio
import logging
from threading import Thread
import queue

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Replace with your bot token
BOT_TOKEN = "7823163314:AAGi3LZ0zFvBvtVauTPtWbcJoLQfQrQfhH0"
WEBHOOK_URL = "https://292c-210-1-49-170.ngrok-free.app/webhook"

# Define conversation states
WAITING_FOR_ADDRESS = 1
WAITING_FOR_FOOD_SELECTION = 2

# Dictionary to store user data
user_data = {}

# Initialize Flask and Application
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# Create a queue for updates
update_queue = queue.Queue()

# Define command handler for /start
async def start(update: Update, context) -> int:
    logger.debug("Start command received")
    username = update.message.from_user.first_name
    
    await update.message.reply_text(
        f"{username}, Welcome to Eat With Cat! 👋\n\n"
        "Powered by AI, Cat will help you satisfy your cravings for yummy dishes without needing to browse delivery apps.\n\nLet Cat know what food you're craving right now!"
    )
    return WAITING_FOR_FOOD_SELECTION

async def collect_food(update: Update, context) -> int:
    user_id = update.message.from_user.id
    food = update.message.text
    
    # Initialize user data if not exists
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # Update the existing dictionary instead of creating a new one
    user_data[user_id]['food_choice'] = food
    
    await update.message.reply_text(
        f"Wonderful choice, let's get some {food}! I've saved your selection. ✅\n\n"
        f"Now what's your address? Cat will find the best {food} in your area! "
    )
    
    logger.info(f"Current user_data: {user_data}")
    
    return WAITING_FOR_ADDRESS

async def collect_address(update: Update, context) -> int:
    user_id = update.message.from_user.id
    address = update.message.text
    
    # Initialize user data if not exists
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # Update the existing dictionary instead of overwriting it
    user_data[user_id]['address'] = address
    
    await update.message.reply_text(
        "Perfect! I've saved your address. ✅\n\n"
        "Here's what I have for you:\n"
        f"Address: {user_data[user_id]['address']}\n"
        f"Food Preference: {user_data[user_id]['food_choice']}\n\n"
        f"Cat is looking for the best munchies around you...🐱🌮 take a look at the menu now! "
    )
    
    logger.info(f"Current user_data: {user_data}")
    
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    await update.message.reply_text(
        "Operation cancelled. You can start again with /start command."
    )
    return ConversationHandler.END

# Flask route to handle webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    logger.debug("Webhook endpoint hit")
    try:
        json_data = request.get_json()
        logger.info(f"Received update: {json_data}")
        update_queue.put(json_data)
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}", exc_info=True)
        return "Error processing update", 500

def run_flask():
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)

async def process_updates():
    while True:
        try:
            while not update_queue.empty():
                json_data = update_queue.get()
                update = Update.de_json(json_data, application.bot)
                await application.process_update(update)
                update_queue.task_done()
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)

async def setup_webhook():
    await application.initialize()
    await application.start()
    
    # Delete webhook before setting it again
    await application.bot.delete_webhook()
    
    # Set webhook
    success = await application.bot.set_webhook(url=WEBHOOK_URL)
    if success:
        logger.info(f"Webhook successfully set to {WEBHOOK_URL}")
    else:
        logger.error("Failed to set webhook")
    
    # Verify webhook info
    webhook_info = await application.bot.get_webhook_info()
    logger.info(f"Webhook info: {webhook_info}")

async def main():
    try:
        # conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                WAITING_FOR_FOOD_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, collect_food)
                ],
                WAITING_FOR_ADDRESS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, collect_address)
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="food_choice_conversation",
            persistent=False
        )
        
        # Add conversation handler
        application.add_handler(conv_handler)
        
        # Set up the webhook
        await setup_webhook()
        
        # Start Flask in a separate thread
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Start processing updates
        await process_updates()
            
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        await application.stop()

if __name__ == "__main__":
    asyncio.run(main())