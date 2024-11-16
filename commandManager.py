from flask import Flask, request, redirect, jsonify
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
import asyncio
import logging
from threading import Thread
import queue
import uuid
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your bot token
BOT_TOKEN = "7823163314:AAGi3LZ0zFvBvtVauTPtWbcJoLQfQrQfhH0"
WEBHOOK_URL = "https://00b0-1-47-144-80.ngrok-free.app/webhook"

CLIENT_ID = "ea37fba5-f638-4308-b773-602ecfb9041e"
CLIENT_SECRET = "kenxZP5sNE4EeYQAAxwMna8Qni"
REDIRECT_URI = "https://00b0-1-47-144-80.ngrok-free.app/oauth/callback"

# Coinbase OAuth URLs
COINBASE_AUTH_URL = "https://www.coinbase.com/oauth/authorize"
COINBASE_TOKEN_URL = "https://api.coinbase.com/oauth/token"
COINBASE_ACCOUNT_URL = "https://api.coinbase.com/v2/user"

# Define conversation states
WAITING_FOR_WALLET = 1
WAITING_FOR_FOOD_SELECTION = 2
WAITING_FOR_ADDRESS = 3

# Dictionary to store user data and pending authentications
user_data = {}
pending_auth = {}

# Initialize Flask and Application
app = Flask(__name__)
application = None
update_queue = queue.Queue()

def create_application():
    global application
    application = Application.builder().token(BOT_TOKEN).build()
    return application

def get_wallet_connect_button(user_id):
    state = str(uuid.uuid4())
    pending_auth[state] = user_id
    
    auth_url = f"{COINBASE_AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=wallet:user:read&state={state}"
    keyboard = [[InlineKeyboardButton("Connect Coinbase Wallet", url=auth_url)]]
    return InlineKeyboardMarkup(keyboard)

def send_telegram_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent to {chat_id}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

@app.route("/oauth/callback")
def callback():
    try:
        code = request.args.get("code")
        state = request.args.get("state")
        
        if not code or not state:
            logger.error("Missing code or state parameter")
            return "Authorization failed: Missing parameters", 400
            
        user_id = pending_auth.get(state)
        if not user_id:
            logger.error(f"Invalid state parameter: {state}")
            return "Invalid state parameter!", 400

        token_response = requests.post(
            COINBASE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            return f"Failed to exchange token: {token_response.text}", 400

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return "Failed to retrieve access token!", 400

        user_response = requests.get(
            COINBASE_ACCOUNT_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if user_response.status_code != 200:
            logger.error(f"Failed to fetch user data: {user_response.text}")
            return "Failed to fetch user data!", 400

        coinbase_user_data = user_response.json()
        logger.info(f"Coinbase user data: {coinbase_user_data}")
        
        # Initialize or update user data
        if user_id not in user_data:
            user_data[user_id] = {}
            
        user_data[user_id].update({
            'wallet_connected': True,
            'access_token': access_token,
            'coinbase_name': coinbase_user_data.get('data', {}).get('name')
        })

        send_telegram_message(
            chat_id=user_id,
            text=f"✅ Wallet connected successfully!\nName: {user_data[user_id]['coinbase_name']}\n\nWhat food are you craving right now? 😋"
        )

        del pending_auth[state]

        return """
        <html>
            <body style="text-align: center; padding: 50px;">
                <h1>Wallet Connected Successfully!</h1>
                <p>You can now return to your conversation with the bot in Telegram.</p>
                <script>
                    setTimeout(function() {
                        window.close();
                    }, 3000);
                </script>
            </body>
        </html>
        """

    except Exception as e:
        logger.error(f"Error in callback: {e}", exc_info=True)
        return f"An error occurred during authentication: {str(e)}", 500

@app.route("/favicon.ico")
def favicon():
    return "", 204

async def start(update: Update, context) -> int:
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name
    
    if user_id in user_data and user_data[user_id].get('wallet_connected'):
        await update.message.reply_text(
            f"Welcome back {username}! I see your wallet is already connected.\n"
            "What food are you craving right now? 😋"
        )
        return WAITING_FOR_FOOD_SELECTION
    
    await update.message.reply_text(
        f"Hello {username}! Welcome to Eat With Cat! 🐱👋\n\n"
        "Powered by AI, Cat will help you satisfy your cravings for yummy dishes without needing to browse delivery apps.\n\n"
        "Before we begin, please connect your Coinbase wallet:",
        reply_markup=get_wallet_connect_button(user_id)
    )
    return WAITING_FOR_WALLET

async def check_wallet(update: Update, context) -> int:
    user_id = update.message.from_user.id
    
    # If wallet is connected, treat the message as food selection
    if user_id in user_data and user_data[user_id].get('wallet_connected'):
        food = update.message.text
        user_data[user_id]['food_choice'] = food
        
        await update.message.reply_text(
            f"Wonderful choice, let's get some {food}! I've saved your selection. ✅\n\n"
            f"Now what's your address? Cat will find the best {food} in your area! 🐈🍕"
        )
        return WAITING_FOR_ADDRESS
        
    await update.message.reply_text(
        "Please connect your Coinbase wallet first:",
        reply_markup=get_wallet_connect_button(user_id)
    )
    return WAITING_FOR_WALLET

async def collect_food(update: Update, context) -> int:
    user_id = update.message.from_user.id
    
    if not user_id in user_data or not user_data[user_id].get('wallet_connected'):
        await update.message.reply_text(
            "Please connect your Coinbase wallet first:",
            reply_markup=get_wallet_connect_button(user_id)
        )
        return WAITING_FOR_WALLET
    
    food = update.message.text
    user_data[user_id]['food_choice'] = food
    
    await update.message.reply_text(
        f"Wonderful choice, let's get some {food}! I've saved your selection. ✅\n\n"
        f"Now what's your address? Cat will find the best {food} in your area!"
    )
    
    return WAITING_FOR_ADDRESS

async def collect_address(update: Update, context) -> int:
    user_id = update.message.from_user.id
    address = update.message.text
    
    user_data[user_id]['address'] = address
    
    await update.message.reply_text(
        "Perfect! I've saved your address. ✅\n\n"
        "Here's what I have for you:\n\n"
        f"Wallet: {user_data[user_id].get('coinbase_name')}\n"
        f"Address: {user_data[user_id]['address']}\n"
        f"Food Preference: {user_data[user_id]['food_choice']}\n\n"
        f"Cat is looking for the best munchies around you...🐱🌮 take a look at the menu now!"
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context) -> int:
    await update.message.reply_text(
        "Operation cancelled. You can start again with /start command."
    )
    return ConversationHandler.END

@app.route("/webhook", methods=["POST"])
def webhook():
    if not application:
        logger.error("Application not initialized")
        return "Application not initialized", 500
        
    try:
        json_data = request.get_json()
        logger.info(f"Received webhook data: {json_data}")
        update_queue.put(json_data)
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook endpoint: {e}", exc_info=True)
        return "Error processing update", 500

def run_flask():
    try:
        logger.info("Starting Flask server...")
        app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Error running Flask: {e}", exc_info=True)

async def process_updates():
    while True:
        try:
            if not application:
                logger.error("Application not initialized")
                await asyncio.sleep(1)
                continue
                
            while not update_queue.empty():
                json_data = update_queue.get()
                update = Update.de_json(json_data, application.bot)
                await application.process_update(update)
                update_queue.task_done()
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)

async def setup_application():
    global application
    
    try:
        # Create and initialize application
        application = create_application()
        await application.initialize()
        await application.start()
        
        # Delete existing webhook and set new one
        await application.bot.delete_webhook()
        success = await application.bot.set_webhook(url=WEBHOOK_URL)
        
        if success:
            logger.info(f"Webhook successfully set to {WEBHOOK_URL}")
        else:
            logger.error("Failed to set webhook")
            return False
            
        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                WAITING_FOR_WALLET: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, check_wallet)
                ],
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
        
        application.add_handler(conv_handler)
        
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"Webhook info: {webhook_info}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up application: {e}", exc_info=True)
        return False

async def main():
    try:
        # Setup application first
        setup_success = await setup_application()
        if not setup_success:
            logger.error("Failed to set up application")
            return

        # Start Flask in a separate thread
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Flask thread started")

        # Start processing updates
        logger.info("Starting update processing")
        await process_updates()
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if application:
            await application.stop()

if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)