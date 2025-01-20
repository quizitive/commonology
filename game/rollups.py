import gspread
from fuzzywuzzy import fuzz
from num2word import word

from game.models import AnswerCode


def autorollup_question_answer(question, raw_player_answer):
    """
    Used in instant games, this method buckets a single raw user input into the best match
    based on codings from a previous game. It performs the following operations, in order:

    1. Check to see if this exact raw_answer exists as an AnswerCode for this question (and return)
    2. Loop through each AnswerCodes for this question:
        a. See if the raw_answer is "close_enough()" to the corresponding AnswerCode.raw_string (and return)
        b. Get the fuzzy ratio between the raw_answer and AnswerCode.raw_string and if it the best match
            so far, save it as the fallback code (and continue)
    """

    # all the codes from the live game
    coded_answers = {ac.raw_string: ac.coded_answer for ac in question.coded_answers.all()}
    coded_player_answer = raw_player_answer

    # we've seen this exact string before
    if raw_player_answer in coded_answers:
        coded_player_answer = coded_answers[raw_player_answer]
        return coded_player_answer

    # see if it's "close enough" to any string we've seen before
    best_score = 0
    for raw_string, coded_answer in coded_answers.items():
        if close_enough(raw_player_answer, raw_string, []):
            coded_player_answer = coded_answer
            return coded_player_answer

        # finally find the string it's closest to, within reason
        if (score := fuzz.ratio(raw_player_answer, raw_string)) > best_score:
            best_score = score
            coded_player_answer = coded_answer

    return coded_player_answer


def close_enough(answer, potential_match, context_synonyms):
    """
    A method that handles fuzzy string matches including:
        - capitalization
        - leading/trailing spaces
        - context synonyms (user override)
        - small typos (see fuzz section for rules)
        - spelling out numbers (e.g. 4 and four)
    :param answer: the answer in question
    :param potential_match: a potential match for that word
    :param context_synonyms: a dictionary of potential matches mapped to answers
    :return: Bool
    """

    answer = answer.lower().strip()
    potential_match = potential_match.lower().strip()

    # an exact match
    if potential_match == answer:
        return True

    # it's a context synonym (user override)
    if potential_match in context_synonyms:
        if context_synonyms[potential_match].lower().strip() == answer.lower():
            return True

    # integers must be an exact match
    try:
        int(potential_match)
        return False
    except ValueError:
        pass

    # it's a typo, slightly different, or shortened version (where both strings are 6 or more characters)
    # or if it's a short string, it is a complete subset and has a full ratio greater than 50
    if all(
        (fuzz.partial_ratio(answer.lower(), potential_match.lower()) > 70, len(answer) > 5, len(potential_match) > 5)
    ) or all(
        (fuzz.partial_ratio(answer.lower(), potential_match.lower()) == 100, fuzz.ratio(answer, potential_match) > 50)
    ):
        return True

    # it's like "four" instead of "4"
    else:
        try:
            if word(answer).lower() == potential_match.lower():
                return True
        except Exception:
            pass

    return False


def process_rollups(col_name, raw_counts, user_rollups):
    """
    The engine behind helpful auto-coding for answers not approved by a human.
    Looks for an existing rollup the answer most likely belongs to, and creates
    a new one if it cannot find one.
    """
    rollups = user_rollups.get(col_name, [])
    updated_counts = {}
    processed_rollups = {}
    resolved = {}
    for unique_resp, count in (
        raw_counts.sort_index(axis=0, ascending=False).sort_values(axis=0, ascending=False).items()
    ):

        # this answer was merged into a larger answer
        if unique_resp not in resolved:
            resolved[unique_resp] = True
        else:
            continue

        # get the coding from the rollups sheet if it exists and go to next unique response
        if unique_resp in rollups:
            recode_val = rollups[unique_resp]
            if recode_val in updated_counts:
                updated_counts[recode_val] += count
                processed_rollups[recode_val].append(unique_resp)
            else:
                updated_counts[recode_val] = count
                processed_rollups[recode_val] = [unique_resp]
            continue

        # this unique response doesn't have a coding associated in the Google Sheet
        # let's see if it seems like a match to an existing rollup
        is_merged = False
        for rollup_name in list(processed_rollups.keys()):
            if close_enough(unique_resp, rollup_name, rollups):
                is_merged = True
                recode_val = rollup_name
                if recode_val in updated_counts:
                    updated_counts[recode_val] += count
                    processed_rollups[recode_val].append(unique_resp)
                else:
                    updated_counts[recode_val] = count
                    processed_rollups[recode_val] = [unique_resp]
                break

        if is_merged:
            continue

        # this unique response has not been coded and doesn't look like anything we've seen
        # so we make it its own category
        processed_rollups[unique_resp] = [unique_resp]
        updated_counts[unique_resp] = count

    return updated_counts, processed_rollups


# all the merged answers, with auto codes where needed
def build_answer_codes(df, rollups_dict):
    answer_codes = {}
    optional_cols = [c for c in df.columns if c.startswith("OPTIONAL: ")]
    for col in df.iloc[:, 3:]:
        counts = df[col].value_counts()
        _, col_answer_codes = process_rollups(col, counts, rollups_dict)
        answer_codes[col] = col_answer_codes
    return answer_codes


def answer_merges(game):
    game_merges = {}
    for q_text in game.questions.values_list("text", flat=True):
        game_merges[q_text] = question_merges(game, q_text)
    return game_merges


def question_merges(game, q_text):
    coded_answers = AnswerCode.objects.filter(question__game=game, question__text=q_text)
    q_merges = {}
    for ca in coded_answers:
        if ca.coded_answer not in q_merges:
            q_merges[ca.coded_answer] = [ca.raw_string]
        else:
            q_merges[ca.coded_answer].append(ca.raw_string)
    return q_merges


def get_user_rollups(sheet_doc):
    # add the sheet if it doesn't exist
    try:
        sheet_doc.add_worksheet("[auto] rollups", 500, 100)
    except gspread.exceptions.APIError:
        pass

    user_rollups = sheet_doc.values_get(range="[auto] rollups", params={"major_dimension": "COLUMNS"}).get("values")

    return user_rollups


def build_rollups_dict(user_rollups):
    if not user_rollups:
        return {}
    rollups = {}
    for col_idx in range(0, len(user_rollups) + 1, 4):
        unique_string_col = user_rollups[col_idx]
        coding_col = user_rollups[col_idx + 1]
        question_text = unique_string_col[0].strip()
        unique_strings_codings = zip(unique_string_col[2:], coding_col[2:])
        rollups[question_text] = {unique_string: coding for unique_string, coding in unique_strings_codings}
    return rollups
