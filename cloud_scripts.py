from gspread_dataframe import get_as_dataframe, set_with_dataframe
from oauth2client import client
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
PROGRAM_PATH = ABS_PATH + "/data/"


def next_available_row(sheet, wsheet):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        PROGRAM_PATH+"googleCreds.json", scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)

    worksheet = spreadsheets.worksheet(wsheet)
    str_list = list(filter(None, worksheet.col_values(1)))
    return str(len(str_list)+1)


def modify_data_worksheet(df, row, sheet, wsheet):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        PROGRAM_PATH+"googleCreds.json", scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)

    worksheet = spreadsheets.worksheet(wsheet)
    set_with_dataframe(worksheet, df, row=row,
                       include_index=True, include_column_header=True)

def read_cloud_df(sheet, wsheet):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        PROGRAM_PATH+"googleCreds.json", scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)

    worksheet = spreadsheets.worksheet(wsheet)
    df = get_as_dataframe(worksheet)
    if 'Unnamed: 0' in df:
        df = df.drop(columns='Unnamed: 0')
    df = df.dropna(how='all')
    df = df.dropna(axis=1, how='all')

    return df.reset_index(drop=True)

def add_hyperlink(sheet, wsheet, cell, link):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(PROGRAM_PATH+
                                                "googleCreds.json", scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)

    worksheet = spreadsheets.worksheet(wsheet)
    cell_value = worksheet.acell(cell).value
    worksheet.update_acell(cell,'=HYPERLINK("%s";"%s")' %(link, cell_value))

def update_cell(sheet, wsheet, cell, value):
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(PROGRAM_PATH+
                                                "googleCreds.json", scope)
    client = gspread.authorize(creds)
    spreadsheets = client.open(sheet)

    worksheet = spreadsheets.worksheet(wsheet)
    worksheet.update_acell(cell, value)