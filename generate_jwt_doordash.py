from os import access
import jwt.utils
import time
import math
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Access the DOORDASH_SIGNING_SECRET variable
signing_secret = os.getenv("DOORDASH_SIGNING_SECRET")
developer_id = os.getenv("DOORDASH_DEVELOPER_ID")
key_id = os.getenv("DOORDASH_KEY_ID")

token = jwt.encode(
    {
        "aud": "doordash",
        "iss": developer_id,
        "kid": key_id,
        "exp": str(math.floor(time.time() + 600)),
        "iat": str(math.floor(time.time())),
    },
    jwt.utils.base64url_decode(signing_secret),
    algorithm="HS256",
    headers={"dd-ver": "DD-JWT-V1"})

print(token)