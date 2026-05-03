# 🤖 WhatsApp Voice Bot

A smart AI-powered WhatsApp voice bot built with **Django**, **OpenAI Whisper**, **Google Gemini**, **gTTS**, **Twilio**, and **Cloudinary**. Users can send a **voice note** on WhatsApp and the bot will:

1. 🎙️ Transcribe the voice note using **Whisper** (Speech-to-Text)
2. 🧠 Generate an intelligent reply using **Google Gemini 2.0 Flash**
3. 🔊 Convert the reply to a voice note using **gTTS** (Text-to-Speech)
4. ☁️ Upload the audio to **Cloudinary**
5. 📤 Send the voice note back to the user via **Twilio WhatsApp API**

The bot also supports plain **text messages** and replies accordingly.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Architecture & Flow](#-architecture--flow)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [Database](#-database)
- [Deployment](#-deployment)
- [How It Works (In Detail)](#-how-it-works-in-detail)

---

## ✨ Features

- 🎤 **Voice Message Support** — Users can send OGG voice notes on WhatsApp
- 🌐 **Multilingual** — Detects language (English / Hindi / Hinglish) and replies in the same language
- 🔁 **Voice-to-Voice** — Receives voice, thinks, replies with voice
- 💬 **Text Fallback** — If voice upload fails, sends a text reply
- 💾 **Conversation Logging** — Every conversation is stored in MongoDB
- 🚀 **Cloud-Ready** — Dockerized, deployable on Heroku / Railway / Render

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | Django 4.x | Web server, routing, settings management |
| **API Layer** | Django REST Framework | RESTful API structure |
| **Speech-to-Text** | OpenAI Whisper (`tiny` model) | Transcribes WhatsApp voice notes (OGG) to text |
| **AI / LLM** | Google Gemini 2.0 Flash | Generates intelligent, context-aware replies |
| **Text-to-Speech** | gTTS (Google Text-to-Speech) | Converts AI reply text into MP3 audio |
| **WhatsApp API** | Twilio | Receives & sends WhatsApp messages and media |
| **Media Storage** | Cloudinary | Hosts generated MP3 voice files publicly |
| **Database (NoSQL)** | MongoDB + MongoEngine | Stores conversation history |
| **Database (SQL)** | SQLite3 | Django's default DB for sessions/admin |
| **Environment Config** | python-dotenv | Loads secrets from `.env` file |
| **Server** | Gunicorn | WSGI production server |
| **Containerization** | Docker | Consistent environment across machines |
| **Deployment** | Heroku (Procfile) | Cloud hosting |

---

## 📁 Project Structure

```
whatsapp-voice-bot/
│
├── voicebot/                   # Django project config (settings, URLs, WSGI)
│   ├── __init__.py
│   ├── settings.py             # All settings: DB, API keys, installed apps
│   ├── urls.py                 # Root URL configuration
│   ├── asgi.py                 # ASGI entry point
│   └── wsgi.py                 # WSGI entry point (used by Gunicorn)
│
├── chatbot/                    # Main Django app — core bot logic
│   ├── __init__.py
│   ├── admin.py                # Django admin registration
│   ├── apps.py                 # App configuration
│   ├── models.py               # MongoDB Conversation model (MongoEngine)
│   ├── urls.py                 # App-level URL: /chatbot/webhook/
│   ├── views.py                # 🔑 Core logic: webhook, transcription, AI, TTS
│   ├── tests.py                # Test cases
│   └── migrations/             # Django migration files (for SQLite)
│
├── manage.py                   # Django management CLI
├── requirements.txt            # All Python dependencies
├── Dockerfile                  # Docker container configuration
├── Procfile                    # Heroku deployment command
├── runtime.txt                 # Python runtime version for Heroku
├── db.sqlite3                  # SQLite database (local only, gitignored)
├── .env                        # Secret keys (gitignored — NEVER commit this!)
├── .gitignore                  # Files excluded from git
└── venv/                       # Python virtual environment (gitignored)
```

---

## 🔄 Architecture & Flow

```
User sends WhatsApp message (Voice/Text)
            │
            ▼
     Twilio Webhook → POST /chatbot/webhook/
            │
            ▼
     ┌──────────────────────────────┐
     │ Is it a voice message?       │
     │  (NumMedia > 0)              │
     └──────────┬───────────────────┘
                │ YES                     │ NO
                ▼                         ▼
     Download OGG audio            Read text from Body
     from Twilio MediaUrl
                │
                ▼
     OpenAI Whisper (tiny)
     → Transcribe OGG → Text
                │
                ▼
     Google Gemini 2.0 Flash
     → Generate AI reply (max 2 sentences)
                │
                ▼
     gTTS (Google TTS)
     → Convert reply text → MP3 file
                │
                ▼
     Cloudinary Uploader
     → Upload MP3 → Get public URL
                │
                ▼
     Save to MongoDB (Conversation log)
                │
                ▼
     Twilio API → Send voice note
     (or text if audio upload failed)
            back to user on WhatsApp
```

---

## ✅ Prerequisites

Before you begin, make sure you have:

- Python **3.11+**
- [FFmpeg](https://ffmpeg.org/download.html) installed and in PATH (required by Whisper)
- A **Twilio** account with WhatsApp sandbox enabled
- A **Google AI Studio** account with Gemini API key
- A **Cloudinary** account
- A **MongoDB Atlas** cluster (free tier works fine)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/whatsapp-voice-bot.git
cd whatsapp-voice-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Installing Whisper will also download the `tiny` model (~39MB) on first run.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
GEMINI_API_KEY=your-gemini-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
```

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

### 7. Expose Locally with ngrok (for Twilio Webhook)

```bash
ngrok http 8000
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`) and set it as your Twilio WhatsApp sandbox webhook:

```
https://abc123.ngrok.io/chatbot/webhook/
```

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (keep this secret!) |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | Google Gemini AI API key |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |

> ⚠️ **Never commit your `.env` file to Git!** It's already included in `.gitignore`.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chatbot/webhook/` | Twilio WhatsApp webhook — handles all incoming messages |
| `GET/POST` | `/admin/` | Django admin panel |

### Webhook Payload (Twilio sends these fields)

| Field | Description |
|-------|-------------|
| `From` | Sender's WhatsApp number (e.g., `whatsapp:+91XXXXXXXXXX`) |
| `Body` | Text content of the message |
| `NumMedia` | Number of media attachments |
| `MediaUrl0` | URL to the voice note (OGG format) |

---

## 🗄️ Database

This project uses **two databases**:

### 1. SQLite3 (Django Default)
- Used for Django internals: sessions, admin, auth
- File: `db.sqlite3` (local only)

### 2. MongoDB (via MongoEngine)
- Used for storing conversation history
- Connected via `mongoengine.connect()` in `settings.py`
- Model:

```python
class Conversation(Document):
    user_phone   = StringField()   # WhatsApp number of user
    user_message = StringField()   # What the user said
    bot_reply    = StringField()   # What the bot replied
    timestamp    = DateTimeField() # When it happened
```

---

## 🐳 Deployment

### Docker

```bash
# Build image
docker build -t whatsapp-voice-bot .

# Run container
docker run -p 8000:8000 --env-file .env whatsapp-voice-bot
```

### Heroku

```bash
heroku create your-app-name
heroku config:set SECRET_KEY=... GEMINI_API_KEY=... # (set all env vars)
git push heroku main
```

The `Procfile` runs:
```
web: gunicorn voicebot.wsgi --log-file -
```

The `runtime.txt` specifies:
```
python-3.11.x
```

---

## 🧠 How It Works (In Detail)

### 1. `whatsapp_webhook` — The Main Handler
The heart of the application. Called every time a WhatsApp message arrives via Twilio. It:
- Checks if there's a media attachment (voice note)
- Downloads and saves the OGG file temporarily
- Routes to the correct processing pipeline

### 2. `transcribe_audio` — Whisper STT
- Uses OpenAI Whisper's `tiny` model (loaded once at startup for performance)
- Directly processes `.ogg` files — no format conversion needed
- Returns transcribed text

### 3. `get_gemini_reply` — AI Brain
- Calls Google Gemini 2.0 Flash REST API
- Prompt instructs the model to:
  - Auto-detect language (English / Hindi / Hinglish)
  - Reply in the same language
  - Keep response to max 2 sentences
  - Sound like a helpful friend
- `clean_response()` strips markdown symbols (`**`, `*`, `#`) for clean spoken audio

### 4. `text_to_voice` — gTTS + Cloudinary
- Converts the AI reply to MP3 using Google TTS
- Uploads MP3 to Cloudinary (under the `voicebot/` folder)
- Returns the public HTTPS URL of the audio file

### 5. `send_whatsapp_voice` — Twilio Delivery
- Uses Twilio Python SDK to send back a WhatsApp message
- If audio URL exists → sends it as a voice media message
- If audio failed → falls back to sending the text reply

---

## 📦 Key Dependencies

```
django              — Web framework
djangorestframework — REST API support
openai-whisper      — Speech recognition (STT)
gTTS                — Text-to-speech (TTS)
twilio              — WhatsApp messaging API
cloudinary          — Audio file hosting
mongoengine         — MongoDB ODM
python-dotenv       — Environment variable loader
gunicorn            — Production WSGI server
requests            — HTTP client for Gemini API & media download
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

## 👨‍💻 Author

**Shivam** — Building cool stuff with AI 🚀

> If you found this project useful, give it a ⭐ on GitHub!
