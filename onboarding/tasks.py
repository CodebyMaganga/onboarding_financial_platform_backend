# tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def send_log_notification(user_id, title, message, timestamp):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "content": {
                "title": title,
                "message": message,
                "timestamp": timestamp,
            },
        },
    )
