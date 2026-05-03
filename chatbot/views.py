import os
import re
import uuid
import requests
import tempfile
import whisper
import warnings
import cloudinary
import cloudinary.uploader
from gtts import gTTS
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from .models import Conversation

warnings.filterwarnings("ignore")

# Cloudinary config
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

# Whisper model ek baar load karo
print("Loading Whisper model...")
WHISPER_MODEL = whisper.load_model("tiny")
print("Whisper model loaded!")


def clean_response(text):
    text = text.replace('`', '')
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#+ ', '', text)
    text = ' '.join(text.split())
    return text


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        print("=== POST DATA ===")
        print(dict(request.POST))
        try:
            from_number = request.POST.get('From', '')
            num_media = int(request.POST.get('NumMedia', 0))

            if num_media > 0:
                media_url = request.POST.get('MediaUrl0', '')
                audio_response = requests.get(
                    media_url,
                    auth=(
                        settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN
                    )
                )
                temp_audio_path = os.path.join(
                    tempfile.gettempdir(),
                    f"{uuid.uuid4()}.ogg"
                )
                with open(temp_audio_path, 'wb') as f:
                    f.write(audio_response.content)

                user_text = transcribe_audio(temp_audio_path)
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
            else:
                user_text = request.POST.get('Body', '')

            if not user_text or user_text.strip() == "":
                user_text = "Hello"

            print(f"User said: {user_text}")

            ai_reply = get_gemini_reply(user_text)
            print(f"AI reply: {ai_reply}")

            audio_url = text_to_voice(ai_reply)
            print(f"Audio URL: {audio_url}")

            try:
                Conversation(
                    user_phone=from_number,
                    user_message=user_text,
                    bot_reply=ai_reply
                ).save()
            except Exception as e:
                print(f"MongoDB save error: {e}")

            send_whatsapp_voice(from_number, audio_url, ai_reply)
            return HttpResponse("OK", status=200)

        except Exception as e:
            print(f"Main Error: {e}")
            return HttpResponse(f"Error: {e}", status=500)

    return HttpResponse("Method not allowed", status=405)


def transcribe_audio(audio_path):
    try:
        # Whisper directly ogg handle karta hai — pydub ki zaroorat nahi!
        result = WHISPER_MODEL.transcribe(audio_path, fp16=False)
        text = result["text"].strip()
        print(f"Transcribed text: {text}")
        return text if text else "Samajh nahi aaya!"
    except Exception as e:
        print(f"Transcribe error: {e}")
        return "Samajh nahi aaya!"


def get_gemini_reply(user_text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are a helpful AI assistant. Detect the language of the user's message and reply in the SAME language.

Rules:
- If user speaks in English → Reply in English
- If user speaks in Hindi → Reply in pure Hindi
- If user speaks in Hinglish → Reply in Hinglish
- Keep reply SHORT — maximum 2 sentences only
- Sound like a helpful friend

User said: {user_text}"""
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 100,
                "temperature": 0.7
            }
        }
        response = requests.post(url, json=payload)
        data = response.json()
        print(f"Gemini raw response: {data}")

        if 'candidates' in data:
            reply = data['candidates'][0]['content']['parts'][0]['text']
            return clean_response(reply)
        else:
            return "Sorry yaar, abhi busy hai — thodi der baad try karo!"
    except Exception as e:
        print(f"Gemini error: {e}")
        return "Sorry, kuch gadbad ho gayi!"


def text_to_voice(text):
    try:
        temp_path = os.path.join(
            tempfile.gettempdir(),
            f"{uuid.uuid4()}.mp3"
        )
        tts = gTTS(text=text, lang='hi')
        tts.save(temp_path)

        upload_result = cloudinary.uploader.upload(
            temp_path,
            resource_type="video",
            folder="voicebot"
        )
        try:
            os.remove(temp_path)
        except:
            pass
        return upload_result['secure_url']
    except Exception as e:
        print(f"TTS error: {e}")
        return None


def send_whatsapp_voice(to_number, audio_url, text_reply):
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        if audio_url:
            client.messages.create(
                from_='whatsapp:+14155238886',
                to=to_number,
                media_url=[audio_url]
            )
        else:
            client.messages.create(
                from_='whatsapp:+14155238886',
                to=to_number,
                body=text_reply
            )
    except Exception as e:
        print(f"Twilio send error: {e}")