from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
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

# Initialize Flask and Application
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# Create a queue for updates
update_queue = queue.Queue()

# Define command handler for /start
async def start(update: Update, context) -> None:
    # logger.debug("Start command received")
    await update.message.reply_text("Welcome to Eat With Cat!\n\nPowered by AI, Cat wil help you satisfy your cravings for yummy dishes without needing to browse delivery apps. Let Cat know what food you're craving right now!")

# Define message handler for text messages
async def handle_message(update: Update, context) -> None:
    logger.debug("Message handler triggered")
    user_message = update.message.text
    chat_id = update.message.chat_id
    username = update.message.from_user.username

    logger.info(f"Received message from {username} (chat ID {chat_id}): {user_message}")
    await update.message.reply_text("Thank you for your message!")

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
            await asyncio.sleep(0.1)  # Small delay to prevent CPU overuse
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
        # Register handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
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