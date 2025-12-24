# Redmine Activity Reporter

A Python script to report activity to Redmine (log time and add comments) using the Redmine REST API. Compatible with Redmine 3.4.6.

## Features

- Log time entries to Redmine issues
- Add comments to Redmine issues
- Combine both operations in a single command
- Support for private notes
- Flexible date handling

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:

- `REDMINE_ENDPOINT`: Your Redmine base URL (e.g., `https://redmine.example.com`)
- `REDMINE_API_KEY`: Your Redmine API key
- `REDMINE_REPORT_TO_USER`: Username to mention in comments (optional, used in multiline comment examples)

You can find your API key in Redmine under: **My Account** → **API access key**

Alternatively, you can pass these values as command-line arguments using `--endpoint` and `--api-key`.

## Usage

### Basic Usage

Log time to an issue:
```bash
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9
```

Log time and add a comment:
```bash
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9 --comment "Fixed bug in login module"
```

Log time with a time entry comment:
```bash
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9 --time-comment "Worked on API integration"
```

Add a multiline comment:
```bash
# Using quotes with newlines (bash)
# Note: REDMINE_REPORT_TO_USER environment variable is used for the username
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9 --comment "$REDMINE_REPORT_TO_USER

I have completed the following tasks:
- Fixed bug in login module
- Updated API documentation
- Added unit tests"

# PowerShell syntax (Windows)
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9 --comment "$env:REDMINE_REPORT_TO_USER

I have completed the following tasks:
- Fixed bug in login module
- Updated API documentation
- Added unit tests"

# Or using a variable (bash)
COMMENT="Line 1
Line 2
Line 3"
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 9 --comment "$COMMENT"
```

### Command-Line Arguments

- `--issue`, `-i`: Issue ID (numeric) or issue key (e.g., ISSUEKEY-1) (required)
- `--hours`, `-h`: Number of hours to log (required)
- `--activity-id`, `-a`: Activity type ID (required)
- `--comment`, `-c`: Comment to add to the issue (optional)
- `--time-comment`: Comment for the time entry itself (optional)
- `--spent-on`: Date in YYYY-MM-DD format (defaults to today)
- `--private`: Add comment as private note (requires permissions)
- `--endpoint`: Redmine endpoint URL (overrides REDMINE_ENDPOINT env var)
- `--api-key`: Redmine API key (overrides REDMINE_API_KEY env var)

### Common Activity IDs

- Development: 9, env. var `REDMINE_ACTIVITY_ID_DEVELOPMENT`
- Localization: 65, env. var `REDMINE_ACTIVITY_ID_LOCALIZATION`

There are two env. vars added:

- REDMINE_ACTIVITY_ID_DEVELOPMENT = 9
- REDMINE_ACTIVITY_ID_LOCALIZATION = 65

To find the activity IDs available in your Redmine instance, check the **Administration** → **Enumerations** → **Activities** section.

## Examples

```bash
# Log 2 hours of development work with a comment (using numeric ID)
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 2 --activity-id 8 --comment "Fixed bug in login module"

# Log time for a specific date
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1.5 --activity-id 8 --spent-on 2024-01-15

# Log time with both time entry comment and issue comment
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 3 --activity-id 8 --time-comment "Code review" --comment "Completed code review for PR #456"

# Add a private note
python redmine_activity_reporter.py --issue ISSUEKEY-1 --hours 1 --activity-id 8 --comment "Internal note" --private
```

## API Compatibility

This script is designed for Redmine 3.4.6 and uses the REST API endpoints:
- `POST /time_entries.json` - for logging time
- `PUT /issues/{id}.json` - for adding comments

## Error Handling

The script provides clear error messages if:
- Environment variables are missing
- API requests fail
- Invalid parameters are provided

Exit codes:
- `0`: Success
- `1`: Error occurred
