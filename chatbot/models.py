from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class Conversation(Document):
    user_phone = StringField()
    user_message = StringField()
    bot_reply = StringField()
    timestamp = DateTimeField(default=datetime.now)

    meta = {
        'ordering': ['-timestamp']
    }