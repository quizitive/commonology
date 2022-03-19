import re
import json
import math
from collections import OrderedDict, deque

from celery import shared_task
import pandas as pd

from django.db.models import Sum, Subquery, OuterRef
from django.db import transaction

from project.utils import REDIS, quick_cache, quick_cache_key, redis_delete_patterns, our_now
from users.models import Player, Team
from game.models import Game, AnswerCode, Series
from game.gsheets_api import api_and_db_data_as_df, write_all_to_gdrive, get_sheet_doc
from game.tasks import api_to_db
from game.rollups import get_user_rollups, build_rollups_dict, build_answer_codes
from leaderboard.models import Leaderboard, PlayerRankScore, LeaderboardMessage


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
        game,
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
    REDIS.set(lb_cache_key(game, answer_tally), leaderboard.to_json(), 24 * 60 * 60)
    save_player_rank_scores.delay(leaderboard.to_json(), game.leaderboard.id)
    return leaderboard


def _leaderboard_from_cache(game, answer_tally):
    lb_json = REDIS.get(lb_cache_key(game, answer_tally))
    if not lb_json:
        return None
    return pd.read_json(lb_json)


@shared_task()
@transaction.atomic()
def save_player_rank_scores(lb_json, lb_id):
    leaderboard = pd.read_json(lb_json)
    prs_objs = []
    for pid, rank, score in zip(leaderboard['id'], leaderboard['Rank'], leaderboard['Score']):
        prs_objs.append(
            PlayerRankScore(leaderboard_id=lb_id, player_id=pid, rank=rank, score=score)
        )
    if prs_objs:
        PlayerRankScore.objects.bulk_update_or_create(
            prs_objs, ['rank', 'score'], match_field=('leaderboard_id', 'player_id'))


def lb_cache_key(game, answer_tally):
    return '_'.join(('leaderboard', game.series.slug, str(game.game_id), str(hash(json.dumps(answer_tally)))))


def clear_leaderboard_cache(games):
    """Deletes all leaderboards and answer tallies for the given games"""
    lb_prefixes = [f'leaderboard_{g.series.slug}_{g.game_id}' for g in games]
    lbs_deleted = redis_delete_patterns(*lb_prefixes)
    at_prefixes = [quick_cache_key(build_answer_tally, g) for g in games]
    ats_deleted = redis_delete_patterns(*at_prefixes)
    return lbs_deleted, ats_deleted


def _score_and_rank(leaderboard, lb_cols):
    leaderboard['Score'] = leaderboard[lb_cols].sum(axis=1).astype('int32')
    leaderboard.sort_values('Score', ascending=False, inplace=True, ignore_index=True)
    leaderboard['Rank'] = leaderboard['Score'].rank(method='min', ascending=False).astype('int32')
    return leaderboard


@quick_cache(24 * 60 * 60)
def build_answer_tally(game):
    raw_string_counts = game.valid_raw_string_counts
    answer_subquery = raw_string_counts.filter(raw_string=OuterRef('raw_string')).filter(question=OuterRef('question'))
    answer_counts = AnswerCode.objects.filter(
        question__game=game).order_by('question__number', 'question_id').values(
        'question__text', 'coded_answer').annotate(
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


@quick_cache()
def player_score_rank_percentile(player, game):
    answer_tally = build_answer_tally(game)
    game_leaderboard = build_filtered_leaderboard(game, answer_tally)
    player_result = game_leaderboard[game_leaderboard['id'] == player.id]
    try:
        score = player_result['Score'].values[0]
        rank = player_result['Rank'].values[0]
    except IndexError:
        return None, None, None
    percentile = round(100 * (1 - rank / len(game_leaderboard)))
    return score, rank, percentile


@quick_cache()
def player_rank_in_all_games(player, series):
    games = Game.objects.filter(series=series, leaderboard__publish_date__lte=our_now())
    ranks = OrderedDict()
    for game in games:
        try:
            _, rank, _ = player_score_rank_percentile(player, game)
        except IndexError:
            rank = None
        ranks[game.game_id] = rank
    return ranks


@quick_cache()
def player_top_game_rank(player, series):
    best = math.inf
    best_game_id = None
    for game_id, rank in player_rank_in_all_games(player, series).items():
        if rank and rank < best:
            best = rank
            best_game_id = game_id
    return best_game_id, best


def rank_string(rank):
    if rank is None:
        return "N/A"
    if rank % 100 in (11, 12, 13):
        suffix = 'th'
    elif rank % 10 == 1:
        suffix = "st"
    elif rank % 10 == 2:
        suffix = "nd"
    elif rank % 10 == 3:
        suffix = "rd"
    else:
        suffix = "th"
    rank_str = f"{rank}{suffix}"
    return rank_str


def score_string(score):
    if score is None:
        return "N/A"
    return f"{score}"


def player_leaderboard_message(game, rank, percentile):
    if not rank:
        return "Looks like you missed this game... you'll get 'em next time!"
    num_players = game.players_dict.count()
    message = f"This game you ranked {rank_string(rank)} out of {num_players} players. "
    follow_up = LeaderboardMessage.select_random_eligible(rank, percentile)
    return message + follow_up


@quick_cache()
def winners_of_game(game):
    """Returns the list of player objects that won the given game"""
    return Player.objects.filter(rank_scores__rank=1, rank_scores__leaderboard__game=game)


@quick_cache()
def winners_of_series(slug):
    """Returns the list of player ids that have won a game in a given Series"""
    winners = Player.objects.filter(
        rank_scores__rank=1,
        rank_scores__leaderboard__game__series__slug=slug,
        rank_scores__leaderboard__publish_date__lte=our_now()
    ).values_list(
        'id', flat=True
    )
    return list(winners)


def visible_leaderboards(slug='commonology', limit=10):
    """The most recent N published leaderboards for a given slug are viewable by members"""
    return Leaderboard.objects.filter(
        game__series__slug=slug, publish_date__lte=our_now()
    ).select_related('game').order_by('-game__game_id')[:limit]
