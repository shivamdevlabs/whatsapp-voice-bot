FROM python:3.11-slim

# FFmpeg install karo
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD gunicorn voicebot.wsgi --bind 0.0.0.0:$PORT