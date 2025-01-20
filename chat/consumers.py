import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from chat.models import Comment


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(self.room_group_name, {"type": "chat_message", "message": message})

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["game_id"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        # make sure use is authenticated
        try:
            user_dn = await self.get_user_dn()
        except AttributeError:
            await self.send("You need to log in to join the conversation!")
            return

        # parse payload and save to database
        text_data_json = json.loads(text_data)
        comment = text_data_json["comment"]
        thread_id = int(text_data_json["thread-id"].split("-")[1])
        await self.post_comment_to_db(self.scope["user"], comment, thread_id)

        # Send message to thread
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "thread_comment", "comment": comment, "user_dn": user_dn, "thread_id": thread_id},
        )

    @database_sync_to_async
    def get_user_dn(self):
        return self.scope["user"].display_name

    @database_sync_to_async
    def post_comment_to_db(self, user, comment, thread_id):
        Comment.objects.create(player=user, comment=comment, thread_id=thread_id)
        return

    # Receive message from thread
    async def thread_comment(self, event):
        comment = event["comment"]
        user_dn = event["user_dn"]
        thread_id = event["thread_id"]

        # Send message to WebSocket
        await self.send(
            f'<div id="thread-{thread_id}" hx-swap-oob="beforeend">'
            f'<div class="thread-{thread_id} question-comment w3-row">'
            f"<b>{user_dn}</b>&nbsp&nbsp{comment}</div>"
            f"</div></div>"
        )
