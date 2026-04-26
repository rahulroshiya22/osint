# 🔍 OSINT Dashboard — Telegram Bot Data Bridge

A premium web dashboard that bridges your website with Telegram bots using a userbot (Telethon). It fetches data from 5 Telegram bots and displays results in a beautiful dark-themed dashboard with admin controls and a public API.

## 🚀 Features

- **5 Bot Integrations**: UserID→Number, Number→Info, Aadhaar→Info, Family Lookup, Instagram Downloader
- **Admin Panel**: Approve/ban users manually, view statistics, monitor all requests
- **Public API**: Generate API keys for friends to use programmatically
- **User Authentication**: JWT-based login/register with admin approval workflow
- **Response Caching**: Avoid spamming bots with repeated requests
- **Request History**: Track all lookups with timestamps
- **Beautiful UI**: Dark glassmorphism theme with animations
- **Demo Mode**: Works without Telegram credentials for testing

## 📋 Setup

### 1. Get Telegram API Credentials

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click "API Development Tools"
4. Create an app and note down `API_ID` and `API_HASH`

### 2. Configure Environment

```bash
# Copy the example env file
copy backend\.env.example backend\.env

# Edit with your credentials
notepad backend\.env
```

Set these values in `.env`:
```
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=+91your_phone
JWT_SECRET=some_random_long_string
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 3. Run the Dashboard

**Option 1: Double-click `start.bat`**

**Option 2: Manual**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 4. First Run — Telegram Login

On first run, Telethon will ask for your phone verification code in the terminal. Enter the code sent to your Telegram app. After this, a session file is created and you won't need to log in again.

### 5. Access the Dashboard

Open [http://localhost:8000](http://localhost:8000) in your browser.

- **Default admin**: `admin` / `admin123`

## 🛠️ API Usage

### Authentication
All API requests need a Bearer token (API key):
```
Authorization: Bearer tb_your_api_key_here
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lookup/userid_to_number` | Telegram User ID → Phone Number |
| POST | `/api/lookup/number_to_info` | Phone Number → Person Info |
| POST | `/api/lookup/aadhaar_to_info` | Aadhaar → Personal Info |
| POST | `/api/lookup/aadhaar_to_family` | Aadhaar → Family Info |
| POST | `/api/lookup/instagram_download` | Instagram URL → Video Download |

### Example
```bash
curl -X POST http://localhost:8000/api/lookup/number_to_info \
  -H "Authorization: Bearer tb_your_key" \
  -H "Content-Type: application/json" \
  -d '{"input": "+919876543210"}'
```

## 📁 Project Structure

```
telegram bot/
├── backend/
│   ├── main.py          # FastAPI app + routes
│   ├── userbot.py       # Telethon client + bot config
│   ├── database.py      # SQLite operations
│   ├── auth.py          # JWT + API key auth
│   ├── requirements.txt
│   ├── .env.example
│   └── sessions/        # Telethon session files (auto-created)
├── frontend/
│   ├── index.html       # Main dashboard
│   ├── style.css        # Premium dark theme
│   └── main.js          # Dashboard logic
├── start.bat            # One-click starter
└── README.md
```

## 👑 Admin Features

- ✅ **Approve** new user registrations
- 🚫 **Ban** users to revoke access
- 🗑️ **Delete** user accounts
- 📊 **Statistics** dashboard with live stats
- 📋 **Request logs** from all users
