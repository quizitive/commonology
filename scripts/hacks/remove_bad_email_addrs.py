from django.contrib.auth import get_user_model


bad_addrs = '''
noah.shapiro@pomina.edu
lindsay.foxen@umww.con
rylandcars@ocloud.com
carly.lundy@gmail.xom
tstroup@indy.rr.cm
dana@punchbugggyrealty.com
lori@pointsettenniso.com
sokolm@tntifreworks.com
kterzakis41@mgial.com
paola.m.martinez@lonestar.edu
t.shumate@aol.con
sobelman.jill@gmail.con
sarahbernstein828@gmail.con
missycameron22@gmail.con
carosandler@gmail.con
tandrade607@gamil.com
lizzie_wilcox@yaboo.com
marissamazzella@gmail.con
collinlenoir@gmai.com
morrisonjosiah@hotmsil.com
hefuhrman@gmai.com
jaimelbschell@facebook.com
herwig.nick@gmai.com
karenohen@gmaio.com
doubleob@aol.co
klfrank04@gmaill.com
newmankaileigh@gamil.com
meredithjrobertson@gmail.con
jmicaliz@gmai.com
noragiannini@gmail.con
jblubin27@gmail.con
claired93@gmail.con
phannigan87@gmai.com
'''

bad_addrs = bad_addrs.split()

User = get_user_model()

qs = User.objects.filter(email__in=bad_addrs).all()
for u in qs:
    print(u.email)
    u.subscribed = False
    u.is_active = False
    u.save()
