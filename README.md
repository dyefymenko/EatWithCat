# EatWithCat

1. run `pip install cdp-langchain`
2. setup environment variables.
```
export CDP_API_KEY_NAME="your-cdp-key-name"
export CDP_API_KEY_PRIVATE_KEY=$'your_cdp_private_key' # Remember to add the $ before the key and surround it with single quotes.
export OPENAI_API_KEY="your_openai_key"
export NETWORK_ID="base-sepolia" # Optional, defaults to base-sepolia
```
3. ensure your openai platform api key has money in it.
4. run generate_jwt_doordash.py to generate a JWT for doordash api
5. save it to your .env file as `DOORDASH_JWT = <JWT>`
6. save the `DOORDASH_SIGNING_SECRET`, `DOORDASH_DEVELOPER_ID`, `DOORDASH_KEY_ID`, to .env file.
7. run `python chatbot.py`


## How to start the Telegram bot
1. in terminal 1, run `ngrok http <available port #>`
2. copy ngrok's forwarding URL, i.e. `https://abcd1234.ngrok-free.app`
3. in terminal 2, run curl -X POST "https://api.telegram.org/bot7823163314:AAGi3LZ0zFvBvtVauTPtWbcJoLQfQrQfhH0/setWebhook" -d "url=<step 2 URL>/webhook"
4. check that this succeeded, `curl -X POST "https://api.telegram.org/bot7823163314:AAGi3LZ0zFvBvtVauTPtWbcJoLQfQrQfhH0/getWebhookInfo"`
5. in the response, see that the url is like   `https://abcd1234.ngrok-free.app/webhook`
6. in commandManager.py, update WEBHOOKS_URL to be step 5 url, and REDIRECT_URI to be like `<step 2 URL>/oauth/callback`
7. in Coinbase's developer dashboard, update the OAuth redirect URI to be like "<step 2 URL>/oauth/callback"
8. in terminal 3, run `python commandManager.py`
