from datetime import datetime
from pytz import timezone

import pandas as pd
from celery import shared_task

from django.utils.timezone import make_aware
from django.db import transaction

from game.models import Game, Question, Answer, AnswerCode
from users.models import Player
from mail.tasks import update_mailing_list


@shared_task
def add(x, y):
    return x + y


@shared_task
def api_to_db(filename, responses, answer_codes, update):
    # convert back to dataframe from json (needed for celery)
    if not isinstance(responses, pd.DataFrame):
        responses = pd.read_json(responses)
        responses['Timestamp'] = responses['Timestamp'].astype('string')

    print("starting logging to db")
    game = game_to_db(filename)
    questions_to_db(game, responses)
    players_to_db(responses)
    answers_to_db(game, responses, update)
    answers_codes_to_db(game, answer_codes)
    print("finished logging to db")


@transaction.atomic
def game_to_db(filename):
    game, _ = Game.objects.get_or_create(
        sheet_name=filename,
        defaults={
            'name': filename.replace(" (Responses)", ""),
        }
    )
    staff = Player.objects.filter(is_staff=True)
    game.hosts.add(*staff)
    game.save()
    return game


@transaction.atomic
def questions_to_db(game, responses):
    q_text = responses.columns[3:]
    questions = []
    for qt in q_text:
        if qt.startswith('OPTIONAL: '):
            q_type = Question.op
        # elif any(len(c) > 1 for c in answer_tally[qt][1].values()):
        #     q_type = Question.fr
        else:
            q_type = Question.mc
        q, _ = Question.objects.get_or_create(
            game=game,
            text=qt,
            defaults={'type': q_type}
        )
        questions.append(q)
    return questions


@transaction.atomic
def players_to_db(responses):
    player_list = zip(
        responses['Name'].tolist(),
        responses['Email Address'].tolist()
    )
    for dn, e in player_list:
        _, created = Player.objects.update_or_create(
            email=e,
            defaults={'display_name': dn[:100]}
        )
        if created:
            update_mailing_list.delay(e)


def answers_to_db(game, responses, update=False):
    if update:
        update_answers_in_db(game, responses)
    else:
        new_answers_to_db(game, responses)


@transaction.atomic
def update_answers_in_db(game, responses):
    prev_players = Player.objects.filter(
        answers__question__game=game).values_list('email', flat=True)
    prev_answers = Answer.objects.filter(
        question__game=game, player__email__in=prev_players).values(
        'id', 'question__text', 'raw_string', 'player__email'
    )
    new_answers = []
    for pa in prev_answers:
        new_answer = responses.at[
            int(responses[responses['Email Address'] == pa['player__email']].index[0]),
            pa['question__text']
        ]
        if new_answer != pa['raw_string']:
            pa['raw_string'] = new_answer
            new_answers.append(Answer(
                id=pa['id'],
                raw_string=new_answer
            ))
    Answer.objects.bulk_update(new_answers, ['raw_string'])


@transaction.atomic
def new_answers_to_db(game, responses):
    q_text = responses.columns[3:]
    prev_players = Player.objects.filter(answers__question__game=game).values_list('email', flat=True)
    new_responses = responses[~responses['Email Address'].isin(prev_players)]
    emails = new_responses['Email Address'].tolist()
    players = dict(Player.objects.filter(email__in=emails).values_list('email', 'id'))
    answers = []
    for qt in q_text:
        question = Question.objects.get(text=qt.strip(), game=game)
        q_id, q_type = question.id, question.type
        player_answers = zip(
            new_responses['Timestamp'],
            emails,
            new_responses[qt].tolist()
        )
        ans_objs = [
            Answer(
                timestamp=make_aware(
                    datetime.strptime(t, '%Y-%m-%d %H:%M:%S'),
                    timezone=timezone('US/Eastern')
                ),
                question_id=q_id,
                player_id=players[e],
                raw_string=a
            )
            for t, e, a in player_answers if (a or q_type != Question.op)
        ]
        answers.extend(ans_objs)
    Answer.objects.bulk_create(answers)


@transaction.atomic
def answers_codes_to_db(game, answer_codes):
    answers = []
    for q, r in answer_codes.items():
        questions = {
            q.text: q for q in Question.objects.filter(game=game)
        }
        for code, raw_strings in r.items():
            for raw in raw_strings:
                a = AnswerCode(
                    question=questions[q],
                    raw_string=raw,
                    coded_answer=code
                )
                answers.append(a)
    AnswerCode.objects.bulk_update_or_create(
        answers, ['coded_answer'], match_field=('question', 'raw_string'))
