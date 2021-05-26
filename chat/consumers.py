import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['game_id']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        comment = text_data_json['comment']
        try:
            user = await self.get_user()
        except AttributeError:
            await self.send("You need to log in to join the conversation!")
            return

        # Send message to thread
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'thread_comment',
                'comment': comment,
                'user': user
            }
        )

    @database_sync_to_async
    def get_user(self):
        return self.scope["user"].display_name

    # Receive message from thread
    async def thread_comment(self, event):
        comment = event['comment']
        user = event['user']

        # Send message to WebSocket
        # todo: output simple html
        await self.send(f'<div id="simp_test" hx-swap-oob="beforeend">'
                        f'<div class="question-comment w3-row">'
                        f'<b>{user}</b>&nbsp&nbsp{comment}</div>'
                        f'</div>'
                        f'</div>')
