import os
import uuid
import requests
import tempfile
import whisper
import cloudinary
import cloudinary.uploader
from pydub import AudioSegment
from gtts import gTTS
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from .models import Conversation

# FFmpeg path — Railway pe automatically milega
import shutil
ffmpeg_path = shutil.which("ffmpeg")
if ffmpeg_path:
    AudioSegment.converter = ffmpeg_path
    AudioSegment.ffmpeg = ffmpeg_path
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        AudioSegment.ffprobe = ffprobe_path
else:
    # Windows local development
    AudioSegment.converter = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffmpeg = r"C:\ffmpeg\bin\ffmpeg.exe"
    AudioSegment.ffprobe = r"C:\ffmpeg\bin\ffprobe.exe"

# Cloudinary config
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

# Whisper model ek baar load karo — startup pe
print("Loading Whisper model...")
WHISPER_MODEL = whisper.load_model("tiny")  # tiny = faster than base
print("Whisper model loaded!")

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        try:
            print("=== POST DATA ===")
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
                os.remove(temp_audio_path)
            else:
                user_text = request.POST.get('Body', '')

            if not user_text or user_text.strip() == "":
                user_text = "Hello"  # Default text agar voice samajh na aaye

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

# import warnings
def transcribe_audio(audio_path):
    try:
        audio = AudioSegment.from_file(audio_path, format="ogg")
        wav_path = audio_path.replace('.ogg', '.wav')
        audio.export(wav_path, format='wav')
        
        # Ab har baar load nahi hoga — already loaded hai!
        result = WHISPER_MODEL.transcribe(wav_path, fp16=False)
        os.remove(wav_path)
        text = result["text"].strip()
        print(f"Transcribed text: {text}")
        return text if text else "Samajh nahi aaya!"
    except Exception as e:
        print(f"Transcribe error: {e}")
        return "Samajh nahi aaya!"


def get_gemini_reply(user_text):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""You are a helpful AI assistant. Detect the language of the user's message and reply in the SAME language.
                    Rules:
                    - If user speaks in English → Reply in English (natural, human-like)
                    - If user speaks in Hindi → Reply in Hindi (pure Hindi words, human touch, warm tone)
                    - If user speaks in Hinglish → Reply in Hinglish
                    - Keep reply short — 40-50 sentences only
                    - Sound like a helpful friend, not a robot

                    User said: {user_text}"""
                }]
            }]
        }
        response = requests.post(url, json=payload)
        data = response.json()
        print(f"Gemini raw response: {data}")

        if 'candidates' in data:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Sorry yaar, AI abhi busy hai — thodi der baad try karo!"
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
        os.remove(temp_path)
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
            # Audio nahi bana toh text bhejo
            client.messages.create(
                from_='whatsapp:+14155238886',
                to=to_number,
                body=text_reply
            )
    except Exception as e:
        print(f"Twilio send error: {e}")