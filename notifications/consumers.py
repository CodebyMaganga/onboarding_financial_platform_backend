import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"user_{self.scope['user'].id}"
        
        # Join group for the user
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send(text_data=json.dumps({"message": "Connected to notifications"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from group
    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "title": event.get("title", ""),
            "created_at": event.get("created_at", "")
        }))
