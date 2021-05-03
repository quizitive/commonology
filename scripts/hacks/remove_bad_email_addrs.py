from django.contrib.auth import get_user_model


bad_addrs = '''
themickman&@gmail.com
daanyaa.kumar@gmail.com
cinematalkin@gmail.com
francisco.martizez.oh@gmail.com
katzcoups@gmail.com
jbongiovanniwosniewski@gmail.com
dolente@barstoolsportsbook.com
pagethompson128@gmail.com
hannah.m.csmp@gmail.com
jesscamariebartlett1@gmail.com
laura.dguercio@gmail.com
dlcsrp60@gmail.com
adinabeiner@email.com
dsc1975@verizon.net
cathyriccetto@hotmail.com
hanah.brunsen@gmail.com
rylandcars@icould.com
marymonagle11@gmail.com
jbongiovanniwisnirwski@gmail.com
mcampue29@gmail.com
mayle.s.barr@ey.com
jerryj01@aol.com
jd41579@yahoo.com
nspoe26@gmail.com
marissamazzella@mghus.com
chuckt@elidefire.com
wksteeedley@gmail.com
julie.dienes@sourcemedia.com
kterzaksi41@gmail.com
paul.birdlingmaier@gmail.com
smithsinget@sbcglobal.net
bfw99@aol.com
ameli.mitchell325@gmail.com
hanmah.brunsen@gmail.com
cgerhan@yahoo.com
aaronmarndt@activenetwork.com
mike.a.colandro@exxonmobil.com
daanyaa.kumar@gmail.com
zach.rowe@ibm.com
mcamoue29@gmail.com
laurenlacy77@sbcglobal.net
naughty1121@jhmi.edu
cjschwartx1025@gmail.com
rodiethompson207@gmail.com
jbongiovannowosnoewski@gmail.com
andyholdgate@comcast.net
rattmadman@nps.edu
amalone2@verizon.com
andrewpeimavera@gmail.com
jsssicakbell5694@gmail.com
bp.bolinger@gmail.com
jbongiovannowosniewski@gmail.com
jack177@me.com
guille.wernich@gmail.com
kw9260@yahoo.com
lyanowwl@gmail.com
ckomuati@gmail.com
wksteeedley@gmail.com
cathyriccetto@hotmail.com
'''

bad_addrs = bad_addrs.split()

User = get_user_model()

qs = User.objects.filter(email__in=bad_addrs).all()
for u in qs:
    print(u.email)
    u.subscribed = False
    u.is_active = False
    u.save()
