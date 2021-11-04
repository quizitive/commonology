
import sys
import os
import datetime
import django

path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from users.models import Player
from game.utils import write_winner_certificate
from game.mail import send_prior_winner_notice
from project.utils import our_now
from users.utils import player_log_entry

data = '''64,Emma Himes
64,Ryan Murphy
64,Karen Wilson
64,Laura N
64,Pat Gould
64,Cassie Perez
64,Lillian W
63,Susan S
63,Emma G
62,Maya Plotkin
62,Jessica Wyman
61,Bill Shinehouse
60,Allie Gregory
60,Katie Statler
59,Caroline Wolf
58,Al Stahl
57,Lucy Scholz
56,Matt Lux
55,Ken Griemsmann
55,Josh Rosen
54,Kristin Smith
53,Sherri Sweren
53,Ryan Newman
52,Marla Stanton
52,Laura Zillmer
52,Claire Sheanshang
51,Maggie Bramble
50,Cameron Ellis
49,Ellen O'Malley
49,Molly Maloy
48,Cassie Perez
48,Mickey Hudson
47,Patty Farty
47,Becky Wozny
46,Emily Maitland
45,Sarah Maibach
44,Ellen Sweeney
43,Devin McDonnell
42,Amelia Best
41,Matthew Jackett
41,Tessa Buffington
40,Jaclyn Michael
39,Kat Devlin
38,Mike Estes
37,Joe Hurwitz
36,Devin McDonnell
35,Marsha Alvares
34,Helen Gunn
33,Kevin Mechenbier
32,Ashley Ruegg
32,Jay Gillespie
31,William vanwhy
31,Samma Lamma
31,Katie Akiba
31,Sarah Klass
30,Sal Bigay
29,DIANE ESTES
28,Kathryn Bach
27,Han & Tay
26,Robert Angarone
25,NICK GALLO - 1 Time Feud Winner
24,Hannah Fuhrman
24,Jenna Lucas
24,Valaree Tang
23,Paul Mailhot-Singer
22,Yael Egnal
21,Kat Devlin
20,Julie Hannigan
19,Alexandra Boroson
19,Jane Schulte
18,Claire Dornbush
17,Kristen Campilonga
17,Melanie Cohen
17,Colin Hart
16,Jenna & Jonah
15,Adrienne LaBorde
15,Charlie D
15,Elizabeth E.
15,Hannah VanConnors
15,Laurie Holmes
15,**MATT SOKOL
14,Kerry Steingraber
13,Nicole Gresalfi
12,Kerry Steingraber
11,Brandon Burke
10,AAAARON
9,Sophia Amberson-Meholic
8,Brian Lee
7,Joe Cervone
7,Shelby Allen
6,Kate Sullivan
5,Cassie Perez
4,Allie Gregory
3,Emily Bolyard
2,Kristen Campilonga
1,Anne Crockett
Test Week,Lindsay Bramble
Test Week,Corey Rovzar'''
data = [i.split(',') for i in data.split("\n")]

data = '''Emma Himes,emma.himes@ey.com,64
Ryan Murphy,rmurphy50@gmail.com,64
Karen Wilson,kjoneswilson@hotmail.com,64
Laura N,laura.nielsen@gmail.com,64
Pat Gould,pkgould1@gmail.com,64
Cassie Perez,cassieperez1104@gmail.com,64
Lillian W,lilluwu@gmail.com,64
Susan S,susan.schaefer23@gmail.com,63
Emma G,emmagranzier@gmail.com,63
Emma G,emmgold16@gmail.com,63
Maya Plotkin,mkhuri@yahoo.com,62
Jessica Wyman,jessicawyman@icloud.com,62
Bill Shinehouse,wshinehouse@gmail.com,61
Allie Gregory,acgregory7@gmail.com,60
Katie Statler,kathryn.statler@gmail.com,60
Caroline Wolf,carolinewolf1@gmail.com,59
Al Stahl,alex.stahl@gmail.com,58
Lucy Scholz,scholz.lucy@gmail.com,57
Lucy Scholz,lucy@liveoakcamp.com,57
Matt Lux,matthewlux1@gmail.com,56
Ken Griemsmann,kgriemsmann@gmail.com,55
Josh Rosen,joshua.n.rosen@vanderbilt.edu,55
Kristin Smith,smitkh0@gmail.com,54
Sherri Sweren,sherri.sweren@gmail.com,53
Ryan Newman,rpnewman@gmail.com,53
Marla Stanton,marlastanton1@verizon.net,52
Laura Zillmer,zillmerlaura@gmail.com,52
Claire Sheanshang,claire.e.sheanshang@ey.com,52
Maggie Bramble,maggiebramble@gmail.com,51
Cameron Ellis,cameron.t.ellis@hotmail.com,50
Ellen O'Malley,eomalley@princeton.edu,49
Molly Maloy,mmaloy5@gmail.com,49
Cassie Perez,cassieperez1104@gmail.com,48
Mickey Hudson,mickeyhudson@gmail.com,48
Patty Farty,patricia.morrow@gmail.com,47
Becky Wozny,beckywozny@yahoo.com,47
Emily Maitland,emilywmaitland@gmail.com,46
Sarah Maibach,sarahmaibach@gmail.com,45
Ellen Sweeney,ellsween@gmail.com,44
Devin McDonnell,devinmcd12@gmail.com,43
Amelia Best,ajba2017@mymail.pomona.edu,42
Amelia Best,amelia.best@pomona.edu,42
Amelia Best,amyjoybest@gmail.com,42
Matthew Jackett,mdjackett@gmail.com,41
Tessa Buffington,twbuff@gmail.com,41
Jaclyn Michael,jngeary@gmail.com,40
Kat Devlin,katdevlin26@gmail.com,39
Mike Estes,mde2n@hotmail.com,38
Joe Hurwitz,joe@930.com,37
Devin McDonnell,devinmcd12@gmail.com,36
Marsha Alvares,marsha.alvares@live.com,35
Helen Gunn,hgunn41@gmail.com,34
Kevin Mechenbier,kjmechenbier@gmail.com,33
Ashley Ruegg,aruegg18@gmail.com,32
Jay Gillespie,harry.baker@dayblink.com,32
William vanwhy,willvanwhy@gmail.com,31
Katie Akiba,katie.akiba@gmail.com,31
Sarah Klass,sarah.klass@gmail.com,31
DIANE ESTES,dianelincoln@hotmail.com,29
Kathryn Bach,kathrynbach3@gmail.com,28
Robert Angarone,robbieangarone@gmail.com,26
NICK GALLO - 1 Time Feud Winner,39gallo@cua.edu,25
Hannah Fuhrman,hefuhrman@gmail.com,24
Jenna Lucas,jenna.anderson331@gmail.com,24
Valaree Tang,valaree.tang@gmail.com,24
Paul Mailhot-Singer,pmsa2017@mymail.pomona.edu,23
Yael Egnal,yaelegnal@gmail.com,22
Kat Devlin,katdevlin26@gmail.com,21
Julie Hannigan,114breck@gmail.com,20
Alexandra Boroson,alexandrakrosche@gmail.com,19
Jane Schulte,jane.e.schulte@gmail.com,19
Claire Dornbush,claired93@gmail.com,18
Kristen Campilonga,kmcampilo@gmail.com,17
Melanie Cohen,mesokol24@gmail.com,17
Colin Hart,colin.hollis.hart@gmail.com,17
Jenna & Jonah,jennaraimist@gmail.com,16
Adrienne LaBorde,amlaborde08@gmail.com,15
Hannah VanConnors,hrvanwhy@gmail.com,15
Laurie Holmes,laurie.a.holmes@gmail.com,15
**MATT SOKOL,sokolm@tntfireworks.com,15
Kerry Steingraber,steingraber.kerry@gmail.com,14
Nicole Gresalfi,ngresalfi@gmail.com,13
Kerry Steingraber,steingraber.kerry@gmail.com,12
AAAARON,arokjer@gmail.com,10
Sophia Amberson-Meholic,seamberson@gmail.com,9
Joe Cervone,jcervone1@gmail.com,7
Shelby Allen,shelbyt.allen@gmail.com,7
Kate Sullivan,kcervone@gmail.com,6
Cassie Perez,cassieperez1104@gmail.com,5
Allie Gregory,acgregory7@gmail.com,4
Emily Bolyard,embolyard@gmail.com,3
Kristen Campilonga,kmcampilo@gmail.com,2
Anne Crockett,annerichmond07@gmail.com,1
Lindsay Bramble,lebramble@gmail.com,Test Week
Corey Rovzar,corey.rovzar@gmail.com,Test Week'''

data = [i.split(',') for i in data.split('\n')]
data = [(i[1], i[2]) for i in data]


def do(winner, game_number):
    filename = write_winner_certificate(winner.display_name, our_now(), game_number)
    send_prior_winner_notice(winner, game_number, filename)


# marc = Player.objects.get(email='ms@koplon.com')
# do(marc, 1)

for email, game_number in data:
    players = Player.objects.filter(email=email).all()
    for winner in players:
        if winner.subscribed:
            print(f"{winner.display_name},{game_number}")
            le = player_log_entry(winner, f"Award Certificate sent for game {game_number}.")
            le.action_time = datetime.datetime(2021, 11, 2, 16, 46, 0)
            le.save()
            # do(winner, game_number)
