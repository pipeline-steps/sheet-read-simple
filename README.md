# sheet-read-simple

Read data from Google Sheets using Google Sheets API

## Overview

This pipeline step reads data from Google Sheets workbooks and exports records to JSONL format. It supports:
- Reading from multiple sheets within a workbook
- Filtering sheets by title using regex patterns
- Custom column selection and naming
- Automatic authentication using Application Default Credentials (ADC)

## Docker Image

This application is available as a Docker image on Docker Hub: `pipelining/sheet-read-simple`

### Usage

```bash
docker run -v /path/to/config.json:/config.json \
           -v /path/to/output:/output \
           pipelining/sheet-read-simple:latest \
           --config /config.json \
           --output /output/data.jsonl
```

To see this documentation, run without arguments:
```bash
docker run pipelining/sheet-read-simple:latest
```

## Authentication

This step uses **Application Default Credentials (ADC)** to authenticate with Google Sheets API. You need to:

1. Enable Google Sheets API in your GCP project
2. Create credentials (Service Account or OAuth)
3. Grant the service account access to the Google Sheets you want to read

### GCP Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Google Sheets API**
3. Create a service account or use an existing one
4. Download the service account key (JSON file)
5. Share your Google Sheet with the service account email address

### Local Development

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Kubernetes/Production

In a Kubernetes environment with Workload Identity, the service account credentials are automatically provided.

## Configuration Parameters

| Name         | Required | Description                                           |
|--------------|----------|-------------------------------------------------------|
| workbookId   | X        | Google Sheets workbook ID (from the URL)              |
| titleRegex   |          | Regex pattern to filter sheets by title (default: ".*") |
| columns      |          | Specific columns to read (e.g., "A:D")               |
| columnNames  |          | Custom column names for the data                      |

### Configuration Details

**workbookId**: Extract this from the Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/{workbookId}/edit
```

**titleRegex**: Regular expression to match sheet titles. Examples:
- `".*"` - Match all sheets (default)
- `"Sheet[0-9]+"` - Match "Sheet1", "Sheet2", etc.
- `"Data.*"` - Match sheets starting with "Data"

**columns**: Specify column range in A1 notation:
- `"A:C"` - Columns A through C
- `"A:A"` - Only column A
- If omitted, all columns are read

**columnNames**: List of column names to use:
- `["name", "email", "age"]` - Custom column names
- If omitted, first row is used as header
- Must match the number of columns if `columns` is specified

### Configuration Examples

#### Example 1: Read all sheets

```json
{
  "workbookId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
}
```

This will read all sheets from the workbook, using the first row as column headers.

#### Example 2: Read specific sheets

```json
{
  "workbookId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "titleRegex": "Data.*"
}
```

This will only read sheets whose titles start with "Data".

#### Example 3: Read specific columns with custom names

```json
{
  "workbookId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "titleRegex": "Sheet1",
  "columns": "A:D",
  "columnNames": ["id", "name", "email", "age"]
}
```

This will read only columns A through D from "Sheet1" and name them id, name, email, and age.

## Output Format

The output JSONL file contains one JSON object per row with the following structure:

```json
{
  "column1": "value1",
  "column2": "value2",
  "column3": "value3",
  "_sheet_title": "Sheet1",
  "_sheet_id": 0
}
```

### Output Fields

- All columns from the sheet are included with their respective values
- `_sheet_title`: The title of the sheet this record came from
- `_sheet_id`: The ID of the sheet (0-indexed)

### Output Example

Input Google Sheet "Sales Data":
```
| Name  | Product | Quantity | Price |
|-------|---------|----------|-------|
| Alice | Widget  | 10       | 25.50 |
| Bob   | Gadget  | 5        | 15.00 |
```

Output JSONL:
```jsonl
{"Name":"Alice","Product":"Widget","Quantity":"10","Price":"25.50","_sheet_title":"Sales Data","_sheet_id":0}
{"Name":"Bob","Product":"Gadget","Quantity":"5","Price":"15.00","_sheet_title":"Sales Data","_sheet_id":0}
```

## Error Handling

- If authentication fails, the step will exit with an error
- If the workbook is not found or not accessible, an error will be logged
- Empty sheets will be skipped with a warning
- Sheets that don't match the titleRegex are silently skipped
- Individual sheet errors won't stop processing of other sheets

## Permissions Required

The service account or OAuth credentials need the following permission:
- **Read access** to the Google Sheets workbook

To grant access:
1. Open the Google Sheet
2. Click "Share"
3. Add the service account email
4. Grant "Viewer" or "Editor" access

## Data Types

Note that all values are read as strings from Google Sheets. If you need to convert to specific types (numbers, dates, etc.), you should do this in a downstream processing step.

## Limitations

- All data is read into memory, so very large sheets may cause memory issues
- API rate limits apply (as per Google Sheets API quotas)
- Maximum of 10 million cells per workbook

## Example Workflow

1. Create a Google Sheet with your data
2. Share the sheet with your service account
3. Get the workbook ID from the URL
4. Create a config.json with the workbook ID
5. Run the Docker container
6. Process the output JSONL file with downstream steps
