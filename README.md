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