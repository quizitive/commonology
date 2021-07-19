
from game.models import Answer
from chat.models import Comment
from users.models import PendingEmail, Player

Answer.objects.all().delete()
Comment.objects.all().delete()
PendingEmail.objects.all().delete()
Player.objects.filter(is_superuser=False).all().delete()
