from django.contrib.auth import get_user_model


unsubscribed_members = '''
carlosc205@gmail.com
rladd@bbyo.org
Alitman723@gmail.com
edoardocerpelloni@gmail.com
kristenmartin2@gmail.com
saramulkeen@gmail.com
valeria.litovchenko@cbrands.com
kelsey.socaciu@ascension.org
irenagorski@gmail.com
zrowe@usc.edu
kellyw22@darden.virginia.edu
aprilflower2@aol.com
miabaricevic5@gmail.com
charlottemacdonald14@gmail.com
morellana1450@yahoo.com
jake.handrick@gmail.com
katie.reid1@gmail.com
justincut27@aol.com
laurencsamuel@gmail.com
daphne.chapline@icloud.com
gcollins22@cmc.edu
megan.e.varhola@ey.com
connor.popik@gmail.com
Bborcherts@gmail.com
russell.roering@fleishman.com
katythaler@gmail.com
msafferman@yahoo.com
katiesue392@me.com
daawusi@gmail.com
aprima12@gmail.com
chillinmilan@gmail.com
hallsy98@gmail.com
moranej@gmail.com
mariahogden@gmail.com
alyssaa@google.com
dboone@inspirato.com
alexisdelprete@gmail.com
kidd546@gmail.com
mttran130@gmail.com
samuel.palmer@toyota.com
katharinecurrault@gmail.com
elsepeck@hotmail.com
glader87@aol.com
layken.culver@gmail.com
idlewild18@gmail.com
zrowe13@gmail.com
stacytrac@gmail.com
luisa.esteves@parthenon.ey.com
hellomero@Gmail.com
bluefire34144@icloud.com
aryabhai204@gmail.com
carly.lundy@gmail.com
jscharfstein@cspace.com
schwartz.jason@gmail.com
baecrystal@gmail.com
alovisa01@gmail.com
rachel.moffat@initiative.com
robin.m.tiberio@gmail.com
hillrutan@gmail.com
shravanbhat1990@gmail.com
jrakas4@gmail.com
acprisco90@gmail.com
zrowe@ibm.com
aric.linkins@gmail.com
danielle.monaco88@gmail.com
randyluck@gmail.com
a.wadyka@gmail.com
a.oconnell12@gmail.com
nam.huynh@cbrands.com
michellekbiro@gmail.com
nilesdorn@gmail.com
karatepro@aol.com
petravx@gmail.com
katy@thesiliconalley.com
mike_tikkanen@outlook.com
monicaesmith@comcast.net
abbyroehr@gmail.com
madelinerob8@gmail.com
ewfruin@gmail.com
breannaessenburg@gmail.com
anniefazzio@me.com
emilyegnor@gmail.com
nealmachado12@gmail.com
erynnalexis@gmail.com
arjunvreddy@gmail.com
qnrask@gmail.com
pbuelow@mymail.mines.edu
trevor.hughes@ey.com
tslead92@gmail.com
matthew.prescott@ey.com
rocky.aguirre23@gmail.com
bfriia@gmail.com
kflax45@gmail.com
maryconnors92@gmail.com
ejmolleur@gmail.com
'''

unsubscribed_members = unsubscribed_members.split()

User = get_user_model()

qs = User.objects.filter(email__in=unsubscribed_members).all()
for u in qs:
    if u.subscribed:
        print(f"unsubscribing {u.email}")
        u.subscribed = False
        u.save()
