
import sys
import os
import django
import pydot


path = os.getcwd()
sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()


from users.models import Player


def player_str(p):
    result = '-Unknown-'
    if p.display_name:
        result = p.display_name

    elif p.first_name:
        if p.last_name:
            result = f"{p.first_name} {p.last_name}"
        else:
            result = p.first_name

    else:
        result = p.email

    return result


graph = pydot.Dot(graph_type='digraph')
for p in Player.objects.all():
    if p.referrer:
        referrer = player_str(p.referrer)
        referee = player_str(p)
        graph.add_edge(pydot.Edge(referrer, referee))

print('About to write png file.')

graph.write_pdf("family_tree.pdf")
