from django.contrib.auth import get_user_model


bad_addrs = """
themickman&@gmail.com
"""

bad_addrs = bad_addrs.split()

User = get_user_model()

qs = User.objects.filter(email__in=bad_addrs).all()
for u in qs:
    print(u.email)
    u.subscribed = False
    u.is_active = False
    u.save()
