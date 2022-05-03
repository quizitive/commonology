# Alex created a spreadsheet of all the people who made referrals in past games.
# This script reads them form an excel spreadsheet and saves them to
# the commonology database.

import sys
import os
import django
import openpyxl

path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player


players = Player.objects.all()

fixes = {
    'Akash Jassal': '',
    'Al Hock': 'hockallie@gmail.com',
    'Alex Baker': '',
    'Alexander Boyce': 'alexboyce3@gmail.com',
    'Alex Kenny': 'akenny912@gmail.com',
    'Ali Boroson': 'alexandrakrosche@gmail.com',
    'Allison Campbell': 'akc.campbell@gmail.com',
    'Alyssa Gudenius': 'alyssaapolonio@gmail.com',
    'Amanda Foster': 'amandabattenfoster@gmail.com',
    'Anna Shang': 'asheanshang@gmail.com',
    'Annie Crockett': 'annerichmond07@gmail.com',
    "Annie O'Connell": 'a.oconnell12@gmail.com',
    'Anthony Pampalone': '',
    'Annie Schetinnikova': 'annie.schetinnikova@gmail.com',
    'Becky Steedley': '',
    'Betty Colandro': '',
    'Bonnye Frost Donatelli': '',
    'Brandi Bonner': '',
    'Brett Donnatelli': 'bdon113@gmail.com',
    'Bri Hewett': 'brianna.hewett@ey.com',
    'Brigid Mertz': 'maloyba@gmail.com',
    'Cailin Slattery': 'cailin.ryan.slattery@gmail.com',
    'Carlos Cabrera': 'carlosc205@gmail.com',
    'Carly Pauline': '',
    'Carly Weisen': 'carlyweisen@gmail.com',
    'Charles Mahood': 'cfmii11@optonline.net',
    'Charles/Chuck Thompson': 'chthomp58@gmail.com',
    'Chris West': 'chrisfwest@aol.com',
    'Christina Ellen': '',
    'Christine Sokol': 'sokolchristina@gmail.com',
    'Connor Powers': 'connorpowers5@gmail.com',
    'Connie Bakutes': 'conniemottola@aol.com',
    'Court Short': 'courtshort9@gmail.com',
    'Courtney Todd': '',
    'Dale Byram': '',
    'Dan Borman': 'dborman@gmail.com',
    'Dan Frazier': 'frazierdaniel95@gmail.com',
    'Dan Kirk': 'daniel.lawrence.kirk@gmail.com',
    'Dara': 'damolotsky@gmail.com',
    'Daryl Byram': 'darrylbyram@gmail.com',
    'David tattersall': '',
    'Deb Crisfield': 'dwickcris@yahoo.com',
    'Ellen Clements': 'etclements826@aol.com',
    'Ellen Falci': '',
    'Ellen Loshelle': 'ellen.loeshelle@gmail.com',
    'Elizabeth Anne Myers Altamura': 'bethanne.altamura@gmail.com',
    'Elizabeth Ring': '	elizabethiring@gmail.com',
    'Frantz Alexis': '',
    'gayatri surendranathan': 'surendranathang@gmail.com',
    'Greiner S.': 'dscottgreiner@gmail.com',
    'Isabel': '',
    'Haneen Shalabi': 'hshalabi1@gmail.com',
    'Hannah VanWhy': 'hrvanwhy@gmail.com',
    'Heather Maffioli': 'hreading-maffioli@sandi.net',
    'Jack Bogaerts': 'jbogaerts6@gmail.com',
    'Jake Moffett': 'jj.moffett@gmail.com',
    'Jaime Van Hennik': 'jrvanhennik@hotmail.com',
    'Jennifer Dillon': 'jennifer.dillon01@gmail.com',
    'Jessica Bell': 'jessicakbell5694@gmail.com',
    'Jessica Levine': 'jrl6595@gmail.com',
    'Jessica Reinstein': 'jfreinstein@gmail.com',
    'Jillian Nestor': 'jenestor@umich.edu',
    'Joey Notowitch': 'joey.notowich@gmail.com',
    'John Foley': 'foleyjohn144@gmail.com',
    'Josh Simon': 'joshualouissimon@gmail.com',
    'Julie Halloran': 'jhal998@gmail.com',
    'Kaela Meyers': 'kaelamyers@gmail.com',
    'Katelyn Newman': 'kaitlyngnewman@gmail.com',
    'Katie Button': 'kaitiebutton@gmail.com',
    'Katie Burke': 'burke.kmp@gmail.com',
    'Kathryn and Bradley': 'kathryn.shrout@gmail.com',
    'Keith McClary': '',
    'Kelsey Girffin': '',
    'Kemal Abdel-Hurr': '',
    'Kenny Griemsmann': '',
    'Kevin Schirmacher': 'schirm1124@yahoo.com',
    'Kristen Lavallee': '',
    'Laura Furney Howe': 'lfurney.howe@gmail.com',
    'Lauren Doorneweerd': 'lauren.doorneweerd@gmail.com',
    'Lauren Pearlman': 'lauren.perlman1@ey.com',
    'Lindsay Reef': 'lindseylazarov@gmail.com',
    'Lissa Glasgo': 'lissa.glasgo@gmail.com',
    'Liz Hardesty': 'lizhardesty@gmail.com',
    'Lucy Hernandez': '',
    'Lucy Shaefer': 'lucyjschaefer@gmail.com',
    'Mac Chapin': 'mackenzie.chapin@gmail.com',
    'Madeline Foster': 'maddyfoster2@gmail.com',
    'Maleeha Haroon': 'maleeha.haroon@gmail.com',
    'Mandy Fraysse': 'maddyfraysse@gmail.com',
    'Marty Weissmush': '',
    'Matt Fisher': 'mattfisher2000@comcast.net',
    'Matt Jackett': 'mdjackett@gmail.com',
    'Melissa Seaton Edmonson': 'seaton.melissa@gmail.com',
    'Micha Goldblum': 'goldblumcello@gmail.com',
    'Michael Bakutes': 'mbakutes@gmail.com',
    'Michael Goldman': '',
    'Mike berge': 'heyohberge@gmail.com',
    'Mike stanzinale': 'stanziale.michael@gmail.com',
    'Monica Shores': '',
    'Nancy Clark': '',
    'Nicholas Kunze': 'nkunze22@gmail.com',
    'Paige Riordan': 'paige.riordon@ey.com',
    'Pamela Smitherman': 'pkobylkevich@gmail.com',
    'Pat bollinger': 'pgbollinger1@gmail.com',
    'Pat Clore': 'patrickclore@gmail.com',
    'Paul Mailhot Singer': 'pmsa2017@mymail.pomona.edu',
    'Paula ': '',
    'Philip Buelow': 'pbuelow@mymail.mines.edu',
    'PJ Hannigan': 'hannigan17@gmail.com',
    'Rachel Bass': 'rcbass4@gmail.com',
    'Rachel Illig (Norton)': 'illigrachel@gmail.com',
    'Rachel Lima': '',
    'Rachel Notowitch': 'rachel.notowich@gmail.com',
    'Rachel Kaplan': 'rachelkaplancc@gmail.com',
    'Rachel Norton': '',
    'Rachel Safferman': 'rsafferman1@gmail.com',
    'Ray Bardes': 'ray.bardes@umww.com',
    'Rebecca Klar': 'rebeccaklar1@gmail.com',
    'Rich Knack': 'knackr@gmail.com',
    'Robbie Penzell': 'rpenzell@gmail.com',
    'Ryan Plotkin': 'rplotkin31@gmail.com',
    'Ryan Van Horn': 'ryan.vanhorn12@gmail.com',
    'Salvador Bigay': 'bigaysalvador@gmail.com',
    'Samuel Chinn': 'sam.chinn@arlp.com',
    'Sam Cannon': 'samanthalcannon@gmail.com',
    'Sam Marwaha': 'sammarw@gmail.com',
    'Sam Middleton': 'smiddleton92@gmail.com',
    'samantha.notowich@gmail.com': 'samantha.notowich@gmail.com',
    'Samantha vauldellon': '',
    'Sara McPhilmy': 'smcphilmy@gmail.com',
    'Sarah Antalis': 'sarahantalis@yahoo.com',
    'Sarah Dargen': 'sarahdarg@gmail.com',
    'Sara Anderson': 'sanderson520@yahoo.com',
    'Sarah Bernstein!': 'sarahbernstein828@gmail.com',
    'Scott Lowenstein': '',
    'Sierra': '',
    'Sophia Amberson Meholic': 'seamberson@gmail.com',
    'Sophie Griscom': 'segriscom@gmail.com',
    'Steph Krantz': 'stephanie.b.krantz@gmail.com',
    'Steve Fusco': 'stevefusco24@gmail.com',
    'Stephen Ludwick': 'stephenjludwick@gmail.com',
    'Sydney Thomas': 'sydnifranksthomas@gmail.com',
    'Tatiana': 'tatiana.r.andrade@gmail.com',
    'Taya Carstenson': 'carsfam4@gmail.com',
    'Terrie Clements': 'etclements826@aol.com',
    'Tim Hall': '',
    'TJ Farrell': 'tjfarr311@gmail.com',
    'Yael ': 'yaelegnal@gmail.com',
    'Valerie Grant': 'vgrant617@gmail.com',
    'Victoria Dickerson': 'victoria0305@bellsouth.net',
    'Wendi Frommelt': '',
    'Wendy Johnson': 'wendyj630@gmail.com',
    'Will Mink': 'wrmink@comcast.net',
    'Will Scott': '',
    'Zach Rowe': 'zrowe13@gmail.com',
    'Zach Sullivan': 'zacharysullivan89@gmail.com',
    'Zach Bernstein': 'zabernstein@gmail.com',
    'Zhubin Aghamolla': 'zhubin@930.com',
}

fixes = {k.lower(): v for k, v in fixes.items()}


def find_by_name(name):
    name = name.lower().strip()

    if name in fixes:
        email = fixes[name].strip()
        if not email:
            return None
        p = Player.objects.get(email=email)
        return p

    words = name.split()

    last_name = words[-1]
    first_name = words[0]

    for u in players:
        if name == u.display_name.lower():
            return u
        if last_name == u.last_name.lower() and first_name == u.first_name.lower():
            return u
        if name == u.email.lower():
            return u

    return None


def process_column(w, c):
    r = 1
    referrer = w.active.cell(row=r, column=c).value.strip()
    referrer_obj = find_by_name(referrer)

    if not referrer_obj:
        print('Cannot resolve ', referrer)
        return

    while referrer:
        r += 1
        referee = w.active.cell(row=r, column=c).value
        if not referee:
            break

        p = find_by_name(referee)
        if p:
            if p.referrer:
                print(referee, 'already referred by', p.referrer, 'not changing it to', referrer_obj)
            else:
                p.referrer = referrer_obj
                p.save()
        else:
            print('Referee', referee, 'does not exist.')


def read_sheet(w):
    c = 1
    referrer = w.active.cell(row=1, column=c).value
    while referrer:
        process_column(w, c)
        c += 1
        referrer = w.active.cell(row=1, column=c).value


fn = os.path.join(os.path.join(os.path.expanduser('~')),
                  'commonology/scripts/hacks/',
                  'Kingdoms.xlsx')
ws = openpyxl.load_workbook(fn)

for sheet_name in ws.sheetnames:
    ws.active = ws.sheetnames.index(sheet_name)
    read_sheet(ws)

# Move all from ms@quizitive.com to ms@koplon.com
k = Player.objects.get(email='ms@koplon.com')
q = Player.objects.get(email='ms@quizitive.com')
for p in Player.objects.all():
    if p.referrer == q:
        p.referrer = k
        p.save()
