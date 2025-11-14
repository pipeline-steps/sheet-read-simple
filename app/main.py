import json
import gspread
import pandas as pd
import re
from google.auth import default

# constants
SHEETS_PREFIX = 'https://docs.google.com/spreadsheets/d/'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
INPUT_DIR = 'input/'
OUTPUT_DIR = 'output/'
CONFIG_JSON = INPUT_DIR+'config.json'
PIPE_EXTENSION = '.pipe'
TERMINATION_LOG = '/dev/termination-log'
OUTPUT_PIPES_PREFIX = 'outputPipes:'
SUCCESS_LOG = 'result:success'

# configuration
with open(CONFIG_JSON) as f:
    config = json.load(f)
workbook_id = config["workbookId"]
title_regex = config["titleRegex"]
columns = config["columns"]
column_names = config["columnNames"]

# authorize and open workbook
print("Opening workbook")
cred, _ = default(scopes=SCOPES)
workbook = gspread.authorize(cred).open_by_url(SHEETS_PREFIX + workbook_id)
# iterate over all sheets
stored = []
for sheet in workbook.worksheets():
    # if sheet title matches
    if re.fullmatch(title_regex, sheet.title):
        # get dataframe
        print(f"Sheet {sheet.title}:", end=" ")
        df = pd.DataFrame(sheet.get(columns), columns=column_names)
        print(len(df))
        # write to file in json line format
        filename = sheet.title + PIPE_EXTENSION
        df.to_json(path_or_buf=OUTPUT_DIR + filename, orient='records', lines=True)
        stored.append(filename)
print(f"Extracted {len(stored)} dataframes")
# write comma separated list of outputs termination log
with open(TERMINATION_LOG, 'w') as f:
    f.write(OUTPUT_PIPES_PREFIX+','.join(stored)+'\n')
    f.write(SUCCESS_LOG+'\n')
print(f"Done")
