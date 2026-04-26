import os
import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    print("❌ Please set API_ID and API_HASH in your .env file first.")
    exit(1)

async def main():
    print("Generating Telethon String Session for Render deployment...")
    print("Please follow the prompts to log in.\n")
    
    # We use StringSession("") to start a new session, which will generate a string
    async with TelegramClient(StringSession(""), int(API_ID), API_HASH) as client:
        print("\n✅ Successfully logged in!")
        session_string = client.session.save()
        print("\n" + "="*50)
        print("YOUR SESSION STRING (Keep this secret!):")
        print("="*50)
        print(f"\n{session_string}\n")
        print("="*50)
        print("\nInstructions for Render:")
        print("1. Go to your Render Web Service dashboard")
        print("2. Navigate to the 'Environment' tab")
        print("3. Add a new Environment Variable:")
        print("   Key: SESSION_STRING")
        print("   Value: <paste the string above>")
        print("4. Make sure API_ID and API_HASH are also added in Render environment variables.")

if __name__ == "__main__":
    asyncio.run(main())
