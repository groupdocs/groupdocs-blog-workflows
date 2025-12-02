# Update Workflow Defaults

This tool automatically updates the default values in `create-release-post-draft.yml` workflow file to match the current month and year.

## What it does

- Updates the `version` default (e.g., "25.9") to current year.month format (e.g., "25.12" for December 2025)
- Updates the `title` default (e.g., "September 2025 release") to current month and year (e.g., "December 2025 release")

## Usage

The script is automatically run by the `update-release-draft-defaults.yml` workflow on the 1st of each month.

You can also run it manually:

```bash
python tools/update-workflow-defaults/update_defaults.py
```

## How it works

1. Calculates the current version as `YY.M` where YY is the last 2 digits of the year and M is the month number
2. Calculates the current title as `"{Month} {Year} release"`
3. Updates the workflow file using regex pattern matching
4. Only makes changes if the values are different from current defaults
