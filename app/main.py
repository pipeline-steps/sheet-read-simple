import sys
import re
import gspread
import pandas as pd
from google.auth import default
from steputil import StepArgs, StepArgsBuilder


# Constants
SHEETS_PREFIX = 'https://docs.google.com/spreadsheets/d/'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def read_sheets(step: StepArgs):
    """
    Read data from Google Sheets based on configuration.

    Args:
        step: StepArgs object containing configuration and output handler
    """
    # Get configuration
    workbook_id = step.config.workbookId
    title_regex = step.config.titleRegex if step.config.titleRegex else ".*"
    columns = step.config.columns if step.config.columns else None
    column_names = step.config.columnNames if step.config.columnNames else None

    print(f"Reading from workbook: {workbook_id}")
    print(f"Sheet title regex: {title_regex}")

    # Authorize and open workbook
    try:
        print("Authenticating with Google Sheets API...")
        cred, _ = default(scopes=SCOPES)
        gc = gspread.authorize(cred)
        workbook = gc.open_by_url(SHEETS_PREFIX + workbook_id)
        print(f"Successfully opened workbook: {workbook.title}")
    except Exception as e:
        print(f"Error opening workbook: {e}", file=sys.stderr)
        sys.exit(1)

    # Iterate over all sheets
    all_records = []
    sheets_processed = 0

    for sheet in workbook.worksheets():
        # Check if sheet title matches regex
        if re.fullmatch(title_regex, sheet.title):
            print(f"Processing sheet: {sheet.title}")

            try:
                # Get data from sheet
                if columns:
                    # Get specific columns
                    data = sheet.get(columns)
                else:
                    # Get all data
                    data = sheet.get_all_values()

                if not data:
                    print(f"  Warning: Sheet '{sheet.title}' is empty", file=sys.stderr)
                    continue

                # Create DataFrame
                if column_names:
                    # Use provided column names
                    df = pd.DataFrame(data, columns=column_names)
                else:
                    # Use first row as header
                    if len(data) > 1:
                        df = pd.DataFrame(data[1:], columns=data[0])
                    else:
                        print(f"  Warning: Sheet '{sheet.title}' has no data rows", file=sys.stderr)
                        continue

                # Convert DataFrame to records
                records = df.to_dict(orient='records')

                # Add sheet metadata to each record
                for record in records:
                    record['_sheet_title'] = sheet.title
                    record['_sheet_id'] = sheet.id

                all_records.extend(records)
                sheets_processed += 1
                print(f"  Extracted {len(records)} records")

            except Exception as e:
                print(f"  Error processing sheet '{sheet.title}': {e}", file=sys.stderr)
                continue

    print(f"\nTotal: Processed {sheets_processed} sheets, extracted {len(all_records)} records")

    # Write output
    if all_records:
        step.output.writeJsons(all_records)
        print(f"Successfully wrote {len(all_records)} records to output")
    else:
        print("Warning: No records were extracted", file=sys.stderr)


def validate_config(config):
    """Validate configuration parameters."""
    if not config.workbookId:
        print("Error: Parameter 'workbookId' is required", file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    read_sheets(StepArgsBuilder()
                .output()
                .config("workbookId")
                .config("titleRegex", optional=True)
                .config("columns", optional=True)
                .config("columnNames", optional=True)
                .validate(validate_config)
                .build()
                )
