import os
import pickle

import gspread
import pandas as pd

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def get_or_create_gdrive_token():

    # --- Borrowed from google api docs, used for local development only --- #

    # If modifying these scopes, delete the file token.pickle.
    scopes = ['https://www.googleapis.com/auth/spreadsheets']

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('../token.pickle'):
        with open('../token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('../token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def api_data_to_df(raw_data):
    """
    :param raw_data: Response data as a list of list
    :return: Pandas dataframe with e-mails de-duped, keeping first, and dropping optional questions
    """
    responses = pd.DataFrame(raw_data[1:], columns=[c.strip() for c in raw_data[0]])
    responses.rename(columns={
        'Name (First & Last!)': 'Name',
        'Name (First & Last)': 'Name',
        'Leaderboard Name': 'Name',
        'Name (First & Last - this appears on results leaderboard!)': 'Name',
        'Email': 'Email Address'
    }, inplace=True)
    responses.sort_values('Timestamp', inplace=True)
    responses.drop_duplicates('Email Address', keep='first', inplace=True)
    responses['Email Address'] = responses['Email Address'].str.lower()

    return responses


def write_all_to_gdrive(sheet_doc, responses, answer_tally, answer_codes, leaderboard):
    write_responses_sheet(sheet_doc, responses)
    rollups_and_tallies = build_rollups_and_tallies(answer_tally, answer_codes)
    write_rollups_sheet(sheet_doc, rollups_and_tallies)
    write_summarized_answer_sheet(sheet_doc, rollups_and_tallies)
    write_leaderboard_sheet(sheet_doc, leaderboard)


def write_responses_sheet(sheet_doc, responses):
    writable_responses = [responses.columns.values.tolist()] + responses.values.tolist()
    try:
        sheet = sheet_doc.worksheet("[auto] raw responses")
        sheet_doc.del_worksheet(sheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
    sheet = sheet_doc.add_worksheet("[auto] raw responses", len(writable_responses), 20)
    sheet.update(writable_responses)


def build_rollups_and_tallies(answer_tally, answer_codes):
    return {
        k: (answer_tally[k], answer_codes[k])
        for k in answer_tally.keys()
    }


def write_rollups_sheet(sheet_doc, rollups_and_tallies):
    # write the rollups used back to rollups sheet
    answer_merges_data = make_rollups_sheet(rollups_and_tallies)

    # guaranteed to exist as it was created earlier
    sheet = sheet_doc.worksheet("[auto] rollups")
    sheet.update(answer_merges_data, major_dimension='COLUMNS')


def write_summarized_answer_sheet(sheet_doc, rollups_and_tallies):
    # write the summarized answer sheet
    answers_sheet_data = make_answers_sheet(rollups_and_tallies)
    try:
        sheet = sheet_doc.worksheet("[auto] answers")
        sheet_doc.del_worksheet(sheet)
    except gspread.exceptions.WorksheetNotFound:
        pass
    sheet = sheet_doc.add_worksheet("[auto] answers", 200, 26)
    sheet.update(answers_sheet_data, major_dimension='COLUMNS')


def write_leaderboard_sheet(sheet_doc, leaderboard):
    api_lb = leaderboard.drop(columns=['id', 'is_host'])
    try:
        sheet = sheet_doc.worksheet("[auto] leaderboard")
    except gspread.exceptions.WorksheetNotFound:
        sheet = sheet_doc.add_worksheet("[auto] leaderboard", len(api_lb), 16)
    sheet.update([list(api_lb.columns)] + api_lb.values.tolist())


def make_answers_sheet(rollups_and_tallies):
    # answer with tallies as a list of lists
    sheet_data = []
    for question, data in rollups_and_tallies.items():
        responses = [question]
        counts = [""]
        for resp_count in sorted(data[0].items(), key=lambda x: -x[1]):
            responses.append(resp_count[0])
            counts.append(resp_count[1])
        sheet_data.append(responses)
        sheet_data.append(counts)
    return sheet_data


def make_rollups_sheet(rollups_and_tallies):
    # the rollups used in this game
    sheet_data = []
    for question, data in rollups_and_tallies.items():
        unique_strings = [question, 'Answer']
        resulting_codes = ['', 'Coding']
        rollup_score = ['', 'Score']
        tallies, merges = data
        for coding, unique_string_list in merges.items():
            for u in unique_string_list:
                unique_strings.append(u)
                resulting_codes.append(coding)
                rollup_score.append(int(tallies[coding]))
        sheet_data.extend((unique_strings, resulting_codes, rollup_score, []))
    return sheet_data
