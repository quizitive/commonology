from datetime import datetime
from pytz import timezone
from collections import deque
from copy import deepcopy

import pandas as pd
from celery import shared_task

from django.utils.timezone import make_aware
from django.db import transaction
from game.models import Question, Answer, AnswerCode
from django.contrib.auth import get_user_model


@shared_task
def api_to_db(game, responses, answer_codes, update):
    # convert back to dataframe from json (needed for celery)
    if not isinstance(responses, pd.DataFrame):
        responses = pd.read_json(responses)
        responses["Timestamp"] = responses["Timestamp"].astype("string")

    print("starting logging to db")
    questions_to_db(game, responses)
    players_to_db(game.series, responses)
    answers_to_db(game, responses, update)
    answers_codes_to_db(game, answer_codes)
    print("finished logging to db")


@transaction.atomic
def questions_to_db(game, responses):
    q_text = responses.columns[3:]
    questions = []
    for idx, qt in enumerate(q_text):
        if qt.startswith("OPTIONAL: "):
            q_type = Question.op
        else:
            q_type = Question.ga
        q, _ = Question.objects.get_or_create(game=game, text=qt, defaults={"type": q_type, "number": idx})
        questions.append(q)
    return questions


@transaction.atomic
def players_to_db(series, responses):
    player_list = zip(responses["Name"].tolist(), responses["Email Address"].tolist())
    User = get_user_model()
    for dn, e in player_list:
        p, created = User.objects.update_or_create(email=e, defaults={"display_name": dn[:100]})
        series.players.add(p)


def answers_to_db(game, responses, update=False):
    if update:
        update_answers_in_db(game, responses)
    else:
        new_answers_to_db(game, responses)


@transaction.atomic
def update_answers_in_db(game, responses):
    User = get_user_model()
    prev_players = User.objects.filter(answers__question__game=game).values_list("email", flat=True)
    prev_answers = Answer.objects.filter(question__game=game, player__email__in=prev_players).values(
        "id", "question__text", "raw_string", "player__email"
    )
    new_answers = []
    for pa in prev_answers:
        new_answer = responses.at[
            int(responses[responses["Email Address"] == pa["player__email"]].index[0]), pa["question__text"]
        ]
        if new_answer != pa["raw_string"]:
            pa["raw_string"] = new_answer
            new_answers.append(Answer(id=pa["id"], raw_string=new_answer))
    Answer.objects.bulk_update(new_answers, ["raw_string"])


@transaction.atomic
def new_answers_to_db(game, responses):
    q_text = responses.columns[3:]
    User = get_user_model()
    prev_players = User.objects.filter(answers__question__game=game).values_list("email", flat=True)
    new_responses = responses[~responses["Email Address"].isin(prev_players)]
    emails = new_responses["Email Address"].tolist()
    User = get_user_model()
    players = dict(User.objects.filter(email__in=emails).values_list("email", "id"))
    answers = []
    for qt in q_text:
        question = Question.objects.get(text=qt.strip(), game=game)
        q_id, q_type = question.id, question.type
        player_answers = zip(new_responses["Timestamp"], emails, new_responses[qt].tolist())
        ans_objs = [
            Answer(
                timestamp=make_aware(datetime.strptime(t, "%Y-%m-%d %H:%M:%S"), timezone=timezone("US/Eastern")),
                question_id=q_id,
                player_id=players[e],
                raw_string=a,
            )
            for t, e, a in player_answers
            if (a or q_type == Question.ga)
        ]
        answers.extend(ans_objs)
    Answer.objects.bulk_create(answers)


@transaction.atomic
def answers_codes_to_db(game, answer_codes):
    answers = []
    for q, r in answer_codes.items():
        questions = {q.text: q for q in Question.objects.filter(game=game)}
        for code, raw_strings in r.items():
            for raw in raw_strings:
                a = AnswerCode(question=questions[q], raw_string=raw, coded_answer=code)
                answers.append(a)
    AnswerCode.objects.bulk_update_or_create(answers, ["coded_answer"], match_field=("question", "raw_string"))


def raw_answers_db_to_df(game):
    """
    Accepts many answer objects for players and creates a grid-like list-of-lists
    where each list is for a given player, and includes timestamp, email, display_name
    and the raw_string value for each question in the game
    """
    raw_player_answers = deque(
        game.raw_player_answers.values_list(
            "player__email",
            "player__display_name",
            "timestamp",
            "question__text",
            "raw_string",
        )
    )
    qtext = [q_text for q_text in game.questions.values_list("text", flat=True).order_by("number")]

    raw_answer_data = []
    while raw_player_answers:
        qt_cp = deepcopy(qtext)
        (
            p_id,
            p_dn,
            ts,
            q_text,
            ans,
        ) = raw_player_answers[0]
        ts = ts.astimezone(tz=timezone("US/Eastern"))
        p_data = [ts.strftime("%m/%d/%Y %H:%M:%S"), p_id, p_dn]
        this_p_id = p_id
        while this_p_id == p_id and raw_player_answers:
            next_q = qt_cp.pop(0)
            *_, this_q, ans = raw_player_answers.popleft()
            while this_q != next_q:
                p_data.append(None)
                next_q = qt_cp.pop(0)
            p_data.append(ans)
            if raw_player_answers:
                this_p_id, *_ = raw_player_answers[0]
        raw_answer_data.append(p_data + [""] * (3 + len(qtext) - len(p_data)))

    raw_answers_df = pd.DataFrame(columns=["Timestamp", "Email Address", "Name"] + qtext, data=raw_answer_data)
    return raw_answers_df.sort_values("Timestamp")
