import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

print("Listing models available for this API Key...")
try:
    for model in client.models.list():
        if "flash" in model.name:
            print(f"- {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
