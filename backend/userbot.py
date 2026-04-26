import os
import re
import asyncio
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
SESSION_STRING = os.getenv("SESSION_STRING")

SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)
SESSION_PATH = os.path.join(SESSION_DIR, "userbot")

BOTS = {
    "userid_to_number": {
        "username": "Adi123_newbot",
        "display_name": "UserID to Number",
        "description": "Get phone number from Telegram User ID",
        "icon": "🔢",
        "input_label": "Telegram User ID",
        "input_placeholder": "e.g. 123456789",
    },
    "number_to_info": {
        "username": "AI_AssidtBot",
        "display_name": "Number to Info",
        "description": "Get information from phone number",
        "icon": "📱",
        "input_label": "Phone Number",
        "input_placeholder": "e.g. 1234567890 (No +91, No Space)",
    },
    "aadhaar_to_family": {
        "username": "Aadhar2Family_AKbot",
        "display_name": "Aadhaar to Family",
        "description": "Get family information from Aadhaar number",
        "icon": "👨‍👩‍👧‍👦",
        "input_label": "Aadhaar Number",
        "input_placeholder": "e.g. 123456789012 (No Space)",
    }
}

client: TelegramClient = None
_lock = asyncio.Lock()
_is_connected = False


async def init_userbot():
    global client, _is_connected
    if not API_ID or not API_HASH:
        logger.warning("⚠️  API_ID/API_HASH not set. DEMO mode.")
        return False
    try:
        if SESSION_STRING:
            logger.info("Using StringSession from environment")
            client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
        else:
            client = TelegramClient(SESSION_PATH, int(API_ID), API_HASH)
            
        await client.start(phone=PHONE_NUMBER)
        me = await client.get_me()
        logger.info(f"✅ Userbot connected as: {me.first_name} (@{me.username})")
        _is_connected = True
        return True
    except Exception as e:
        logger.error(f"❌ Failed to connect userbot: {e}")
        _is_connected = False
        return False


async def disconnect_userbot():
    global client, _is_connected
    if client and _is_connected:
        await client.disconnect()
        _is_connected = False


def is_connected():
    return _is_connected


def extract_aadhaar_numbers(text):
    """Extract Aadhaar numbers (12 digits) from text."""
    patterns = [
        r'\b(\d{4}\s\d{4}\s\d{4})\b',
        r'\b(\d{12})\b',
        r'\b(\d{4}-\d{4}-\d{4})\b',
    ]
    results = []
    for p in patterns:
        for m in re.finditer(p, text):
            num = re.sub(r'[\s-]', '', m.group(1))
            if len(num) == 12 and num not in results:
                results.append(num)
    return results


def extract_phone_numbers(text):
    """Extract phone numbers from text."""
    patterns = [
        r'(\+?\d{1,3}[\s-]?\d{10})',
        r'(\+?\d{10,13})',
        r'(\d{5}\s?\d{5})',
    ]
    results = []
    for p in patterns:
        for m in re.finditer(p, text):
            num = re.sub(r'[\s-]', '', m.group(1))
            if len(num) >= 10 and num not in results:
                results.append(num)
    return results


async def send_and_receive(bot_key: str, input_text: str, timeout: int = 45) -> dict:
    """Send a message to a bot and wait for response."""
    global client
    if not _is_connected or not client:
        return _get_demo_response(bot_key, input_text)

    bot_config = BOTS.get(bot_key)
    if not bot_config:
        return {"success": False, "error": f"Unknown bot: {bot_key}"}

    async with _lock:
        try:
            bot_entity = await client.get_entity(bot_config["username"])
            await client.send_message(bot_entity, input_text)
            logger.info(f"📤 Sent to @{bot_config['username']}: {input_text}")

            # Collect multiple messages (bots sometimes send multiple)
            messages = await _collect_responses(bot_entity, timeout)

            if messages:
                result = await _parse_messages(messages, bot_key)
                logger.info(f"📥 Got {len(messages)} msg(s) from @{bot_config['username']}")
                return {"success": True, "data": result, "bot": bot_config["display_name"]}
            else:
                return {"success": False, "error": "Bot did not respond within timeout"}
        except Exception as e:
            logger.error(f"❌ Error with @{bot_config['username']}: {e}")
            return {"success": False, "error": str(e)}


async def _collect_responses(bot_entity, timeout: int) -> list:
    """Collect all response messages from the bot (some bots send multi-msg replies)."""
    bot_id = bot_entity.id
    messages = []
    last_msg_time = asyncio.get_event_loop().time()
    done_event = asyncio.Event()

    @client.on(events.NewMessage(from_users=bot_id))
    async def handler(event):
        nonlocal last_msg_time
        messages.append(event.message)
        last_msg_time = asyncio.get_event_loop().time()

    try:
        # Wait for first message
        start = asyncio.get_event_loop().time()
        while not messages and (asyncio.get_event_loop().time() - start) < timeout:
            await asyncio.sleep(0.5)

        if messages:
            # After first message, keep collecting for 3 more seconds
            await asyncio.sleep(3)
            # Check if more came in
            while (asyncio.get_event_loop().time() - last_msg_time) < 2:
                await asyncio.sleep(1)
    finally:
        client.remove_event_handler(handler)

    return messages


async def _parse_messages(messages: list, bot_key: str) -> dict:
    """Parse one or more Telegram messages into structured data."""
    all_text = []
    media_items = []

    for msg in messages:
        if msg.text:
            all_text.append(msg.text)

        if msg.media:
            if isinstance(msg.media, MessageMediaPhoto):
                try:
                    dl_dir = os.path.join(os.path.dirname(__file__), "downloads")
                    os.makedirs(dl_dir, exist_ok=True)
                    path = await client.download_media(msg, file=dl_dir)
                    media_items.append({
                        "type": "photo",
                        "url": f"/api/media/{os.path.basename(path)}"
                    })
                except Exception as e:
                    logger.error(f"Download photo error: {e}")

            elif isinstance(msg.media, MessageMediaDocument):
                doc = msg.media.document
                mtype = "document"
                fname = None
                for attr in doc.attributes:
                    if hasattr(attr, "file_name"):
                        fname = attr.file_name
                if doc.mime_type and doc.mime_type.startswith("video"):
                    mtype = "video"
                try:
                    dl_dir = os.path.join(os.path.dirname(__file__), "downloads")
                    os.makedirs(dl_dir, exist_ok=True)
                    path = await client.download_media(msg, file=dl_dir)
                    media_items.append({
                        "type": mtype,
                        "url": f"/api/media/{os.path.basename(path)}",
                        "file_name": fname
                    })
                except Exception as e:
                    logger.error(f"Download media error: {e}")

    combined_text = "\n\n".join(all_text)
    cleaned = _clean_text(combined_text)
    parsed = _smart_parse(cleaned, bot_key)
    aadhaar_numbers = extract_aadhaar_numbers(combined_text)

    return {
        "text": cleaned,
        "raw_text": combined_text,
        "parsed": parsed,
        "has_media": len(media_items) > 0,
        "media": media_items,
        "found_aadhaar": aadhaar_numbers,
    }


def _clean_text(text: str) -> str:
    """Remove bot watermarks, @mentions, promo lines, and decorative junk."""
    if not text:
        return ""

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines (keep one max)
        if not stripped:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue

        # Skip lines that are just decorative characters
        deco_chars = set('═─━▬•◦◉⊙✦✧★☆♦♢◇◆╔╚║╠╗╝╣┌└├┐┘┤─━═▬~*_')
        if all(c in deco_chars or c == ' ' for c in stripped):
            continue

        # Skip lines with @ usernames (bot promos/watermarks)
        if re.search(r'@[A-Za-z0-9_]{3,}', stripped):
            continue

        # Skip common bot promo/footer patterns
        skip_patterns = [
            r'(?i)join\s+(our|my)?\s*(channel|group)',
            r'(?i)subscribe',
            r'(?i)powered\s+by',
            r'(?i)made\s+(by|with)',
            r'(?i)bot\s+by',
            r'(?i)developed\s+by',
            r'(?i)creator',
            r'(?i)contact\s+(us|me|admin)',
            r'(?i)share\s+this\s+bot',
            r'(?i)forward\s+to',
            r'(?i)buy\s+premium',
            r'(?i)upgrade\s+to',
            r'(?i)t\.me/',
            r'👨‍💻',
            r'🤖.*bot',
        ]
        skip = False
        for pat in skip_patterns:
            if re.search(pat, stripped):
                skip = True
                break
        if skip:
            continue

        # Skip lines that are just emojis
        emoji_stripped = re.sub(r'[\U00010000-\U0010ffff]', '', stripped).strip()
        if not emoji_stripped:
            continue

        cleaned.append(stripped)

    # Remove trailing empty lines
    while cleaned and cleaned[-1] == "":
        cleaned.pop()

    return "\n".join(cleaned)


def _smart_parse(text: str, bot_key: str) -> dict:
    """Smart parse bot response into structured key-value pairs."""
    parsed = {}
    if not text:
        return parsed

    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip decorative lines or headers
        if all(c in '═─━━═▬▬▬═━─•◦◉⊙✦✧★☆♦♢◇◆' for c in line.replace(' ', '')):
            continue
        if line.startswith(('╔', '╚', '║', '╠', '╗', '╝', '╣', '┌', '└', '├', '┐', '┘', '┤')):
            continue

        # Try to extract key:value pairs
        for sep in [':', '➜', '→', '=>', '=', '»', '|', '-']:
            if sep in line:
                parts = line.split(sep, 1)
                key = parts[0].strip()
                value = parts[1].strip()
                # Clean up key
                key = re.sub(r'^[•\-\*▸▹►◉⊙✦✧★☆♦♢◇◆🔹🔸📌📍🏠🏡📱📞👤👨👩🧑📧📫💰🏢🏛️🪪📋]\s*', '', key).strip()
                key = re.sub(r'\*+', '', key).strip()
                if key and value and len(key) < 50:
                    # Categorize / beautify keys
                    parsed[key] = value
                    break

    return parsed


async def chained_lookup(bot_key: str, input_text: str) -> dict:
    """
    Perform a lookup and if Aadhaar numbers are found,
    automatically look them up in Aadhaar family bot too.
    """
    primary = await send_and_receive(bot_key, input_text)
    if not primary.get("success"):
        return primary

    result = primary
    aadhaar_list = primary["data"].get("found_aadhaar", [])

    if aadhaar_list and bot_key != "aadhaar_to_family":
        # Auto-chain: send to Aadhaar family bot
        chain_results = {}
        for aadhaar in aadhaar_list[:1]:  # Only first Aadhaar to avoid spam
            logger.info(f"🔗 Auto-chain: found Aadhaar {aadhaar}, fetching family details...")

            family = await send_and_receive("aadhaar_to_family", aadhaar)
            if family.get("success"):
                chain_results["aadhaar_family"] = family["data"]

        if chain_results:
            result["chain"] = chain_results
            result["chained_aadhaar"] = aadhaar_list[0]

    return result


def _get_demo_response(bot_key: str, input_text: str) -> dict:
    demo = {
        "userid_to_number": {
            "success": True,
            "data": {
                "text": f"📱 Result for User ID: {input_text}\n\n• Phone: +91 98765 43210\n• Name: Demo User\n• Username: @demouser\n• Status: Active\n• Aadhaar: 1234 5678 9012",
                "parsed": {"Phone": "+91 98765 43210", "Name": "Demo User", "Username": "@demouser", "Status": "Active", "Aadhaar": "1234 5678 9012"},
                "has_media": False, "media": [], "found_aadhaar": ["123456789012"]
            },
            "bot": "UserID to Number", "demo": True
        },
        "number_to_info": {
            "success": True,
            "data": {
                "text": f"📋 Information for: {input_text}\n\n• Full Name: Rahul Sharma\n• State: Maharashtra\n• City: Mumbai\n• Operator: Jio\n• Type: Mobile\n• Aadhaar: 9876 5432 1098",
                "parsed": {"Full Name": "Rahul Sharma", "State": "Maharashtra", "City": "Mumbai", "Operator": "Jio", "Type": "Mobile", "Aadhaar": "9876 5432 1098"},
                "has_media": False, "media": [], "found_aadhaar": ["987654321098"]
            },
            "bot": "Number to Info", "demo": True
        },
        "aadhaar_to_family": {
            "success": True,
            "data": {
                "text": f"👨‍👩‍👧‍👦 Family Info\n\n• Head of Family: Suresh Sharma\n• Member 1: Sunita Sharma (Wife)\n• Member 2: Rahul Sharma (Son)\n• Member 3: Priya Sharma (Daughter)\n• Total Members: 4\n• Ration Card: MH123456",
                "parsed": {"Head of Family": "Suresh Sharma", "Member 1": "Sunita Sharma (Wife)", "Member 2": "Rahul Sharma (Son)", "Member 3": "Priya Sharma (Daughter)", "Total Members": "4", "Ration Card": "MH123456"},
                "has_media": False, "media": [], "found_aadhaar": []
            },
            "bot": "Aadhaar to Family", "demo": True
        },
        "instagram_download": {
            "success": True,
            "data": {
                "text": f"📸 Instagram Video\n\n• URL: {input_text}\n• Status: ✅ Downloaded",
                "parsed": {"URL": input_text, "Status": "✅ Downloaded"},
                "has_media": True, "media": [{"type": "video", "url": "#demo"}], "found_aadhaar": []
            },
            "bot": "Instagram Downloader", "demo": True
        },
    }
    return demo.get(bot_key, {"success": False, "error": "Unknown bot", "demo": True})
