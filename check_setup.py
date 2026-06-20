import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("FRED_API_KEY")
print("Key loaded!" if key else "Key NOT found - check your .env file")
