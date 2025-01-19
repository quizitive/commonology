from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})
