import re
import json
from collections import OrderedDict, deque

import pandas as pd
import gspread

from django.db.models import Sum, Subquery, OuterRef
from django.conf import settings

from project.utils import REDIS, quick_cache
from users.models import Player, Team
from game.models import Game, AnswerCode
from game.gsheets_api import api_and_db_data_as_df, write_all_to_gdrive, get_sheet_doc
from game.tasks import api_to_db
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes


def tabulate_results(game, update=False):
    """
    Reads from, tabulates, and prints output to the named Google Sheet
    :param game: The game object
    :param update: Whether or not to update existing answer records in the DB
    :return: None
    """
    sheet_doc = get_sheet_doc(game)
    responses = api_and_db_data_as_df(game, sheet_doc)

    user_rollups = get_user_rollups(sheet_doc)
    rollups_dict = build_rollups_dict(user_rollups)
    answer_codes = build_answer_codes(responses, rollups_dict)

    # write to database
    api_to_db(
        game.series.slug,
        game.sheet_name,
        responses.to_json(),
        answer_codes,
        update
    )

    # calculate the question-by-question data and leaderboard
    # NOTE: both of these call the method that rebuilds themself from db and clears the cache
    answer_tally = build_answer_tally(game, force_refresh=True)
    leaderboard = build_leaderboard_fromdb(game, answer_tally)

    # write to google
    write_all_to_gdrive(sheet_doc, responses, answer_tally, answer_codes, leaderboard)


def build_filtered_leaderboard(game, answer_tally, player_ids=None, search_term=None, team_id=None):
    """
    Get complete leaderboard from cache or build it, then filter results
    This is the primary leaderboard function
    :param game: Game object on which to calculate leaderboard
    :param answer_tally: The corresponding answer tally
    :param player_ids: A list of player_ids on which to filter
    :param search_term: Comma separated search terms for exact match search (case insensitive)
    :param team_id: A Team ID to filter players on
    :return: A scored, ranked and sorted pandas DataFrame of the Leaderboard
    """
    leaderboard = _build_leaderboard_fromdb_or_cache(game, answer_tally)

    if player_ids is not None:
        leaderboard = leaderboard[leaderboard['id'].isin(player_ids)]

    if search_term:
        leaderboard = leaderboard[leaderboard['Name'].str.contains(
            "|".join([re.escape(q) for q in search_term.split(', ')]), flags=re.IGNORECASE, regex=True)]

    if team_id:
        team = Team.objects.get(id=team_id)
        members = team.players.values_list('id', flat=True)
        leaderboard = leaderboard[leaderboard['id'].isin(members)]
    # else:
    #     # don't show hosts in public leaderboard (they could be perceived as cheating)
    #     hosts = game.hosts.values_list('id', flat=True)
    #     leaderboard = leaderboard[~leaderboard['id'].isin(hosts)]

    return leaderboard


def _build_leaderboard_fromdb_or_cache(game, answer_tally):
    lb = _leaderboard_from_cache(game, answer_tally)
    if lb is None:
        lb = build_leaderboard_fromdb(game, answer_tally)
    return lb


def build_leaderboard_fromdb(game, answer_tally):
    cpas = deque(game.coded_player_answers)
    lb_cols = [
        q_text for q_text in game.game_questions.values_list('text', flat=True)
    ]

    # build list of list to create a dataframe leaderboard
    # there may be a better way with itertools, but this is at least O(n)
    # motivated by a desire to reduce the number of db queries (before it was 1/player)
    lb_data = []

    while cpas:
        p_id, p_dn, q_text, ans, is_adm = cpas[0]
        p_data = [p_id, is_adm, p_dn]
        this_p_id = p_id
        while this_p_id == p_id and cpas:
            _, _, q_text, ans, _ = cpas.popleft()
            try:
                p_data.append(answer_tally[q_text][ans])
            except KeyError:
                # this happens when an answer or player is omitted,
                # and their answer is a unique string
                p_data.append(0)
            if cpas:
                this_p_id, *_ = cpas[0]
        lb_data.append(p_data)

    leaderboard = pd.DataFrame(
        columns=['id', 'is_host', 'Name'] + lb_cols,
        data=lb_data
    )
    leaderboard = _score_and_rank(leaderboard, lb_cols)
    leaderboard = leaderboard[['id', 'is_host', 'Rank', 'Name', 'Score'] + lb_cols]
    REDIS.set(lb_cache_key(game, answer_tally), leaderboard.to_json(), 60 * 60)
    return leaderboard


def _leaderboard_from_cache(game, answer_tally):
    lb_json = REDIS.get(lb_cache_key(game, answer_tally))
    if not lb_json:
        return None
    return pd.read_json(lb_json)


def lb_cache_key(game, answer_tally):
    return '_'.join(('leaderboard', game.series.slug, str(game.game_id), str(hash(json.dumps(answer_tally)))))


def _score_and_rank(leaderboard, lb_cols):
    leaderboard['Score'] = leaderboard[lb_cols].sum(axis=1).astype('int32')
    leaderboard.sort_values('Score', ascending=False, inplace=True, ignore_index=True)
    leaderboard['Rank'] = leaderboard['Score'].rank(method='min', ascending=False).astype('int32')
    return leaderboard


@quick_cache(60 * 60)
def build_answer_tally(game):
    raw_string_counts = game.valid_raw_string_counts
    answer_subquery = raw_string_counts.filter(raw_string=OuterRef('raw_string')).filter(question=OuterRef('question'))
    answer_counts = AnswerCode.objects.filter(
        question__game=game).order_by('question_id').values('question__text', 'coded_answer').annotate(
        score=Sum(Subquery(answer_subquery.values('count')))
    )
    answer_tally = {}
    for a in answer_counts:
        score = a['score'] or 0
        if score == 0:
            continue
        if a['question__text'] not in answer_tally:
            answer_tally[a['question__text']] = {a['coded_answer']: score}
        else:
            answer_tally[a['question__text']][a['coded_answer']] = score

    for q, tally in answer_tally.items():
        answer_tally[q] = OrderedDict(sorted(tally.items(), key=lambda x: -x[1]))
    return answer_tally


def _answer_tally_from_cache(game):
    at_json = REDIS.get(f'answertally_{game.series}_{game.game_id}')
    if not at_json:
        return None
    return json.loads(at_json)


def player_rank_and_percentile_in_game(player_id, series_slug, game_id):
    game = Game.objects.get(game_id=game_id, series__slug=series_slug)
    answer_tally = build_answer_tally(game)
    try:
        rank = build_filtered_leaderboard(game, answer_tally, player_ids=[player_id])['Rank'].values[0]
    except IndexError:
        raise IndexError("The player id does not exist for this game.")
    percentile = rank / game.players_dict.count()
    if rank == 1:
        rank_str = "1st"
    elif rank == 2:
        rank_str = "2nd"
    elif rank == 3:
        rank_str = "3rd"
    else:
        rank_str = f"{rank}th"
    return rank_str, percentile


def winners_of_game(game):
    answer_tally = build_answer_tally(game)
    leaderboard = build_filtered_leaderboard(game, answer_tally)
    player_ids = leaderboard[leaderboard['Rank'] == 1]['id'].tolist()
    return Player.objects.filter(id__in=player_ids)
