# Public Release Post Draft

Generates a complete release blog post by fetching release notes, preparing front matter, creating an LLM prompt, calling the LLM for the body content, and writing the final Markdown file.

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

```bash
py ./create_draft.py \
  --product "GroupDocs.Viewer for .NET" \
  --version "25.9" \
  --title "September 2025 release" \
  --release-notes https://releases.groupdocs.com/viewer/net/release-notes/2025/groupdocs-viewer-for-net-25-9-release-notes/
```

```powershell
python .\create_draft.py `
  --product "GroupDocs.Viewer for .NET" `
  --version "25.9" `
  --title "September 2025 release" `
  --release-notes "https://releases.groupdocs.com/viewer/net/release-notes/2025/groupdocs-viewer-for-net-25-9-release-notes/"
```

## Environment variables

Set the following before running when using the LLM integration:

```powershell
$Env:PROFESSIONALIZE_API_KEY = "<your_api_key>"
$Env:PROFESSIONALIZE_API_URL = "<your_api_url>"
$Env:PROFESSIONALIZE_MODEL_NAME = "<model_name>"  # Optional, defaults to "recommended"
```

```bash
export PROFESSIONALIZE_API_KEY="<your_api_key>"
export PROFESSIONALIZE_API_URL="<your_api_url>"
export PROFESSIONALIZE_MODEL_NAME="<model_name>"  # Optional, defaults to "recommended"
```

Optional logging level (defaults to INFO):

```powershell
$Env:LOG_LEVEL = "DEBUG"
```

```bash
export LOG_LEVEL="DEBUG"
```

## Output

- Final file is written to `tools/public-release-post-draft/output/index.md`.
- The file contains YAML front matter followed by the LLM-generated Markdown body.

Notes:
- The `--release-notes` URL should point to the public release notes page. The tool extracts the inner HTML of `<section role="main">` as the source.
- Set both `PROFESSIONALIZE_API_KEY` and `PROFESSIONALIZE_API_URL` to enable the LLM call.
