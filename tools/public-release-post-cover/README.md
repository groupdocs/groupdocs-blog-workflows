# Public Release Post Cover 

Generates cover image for the public release post e.g. <https://blog.groupdocs.com/total/groupdocs-total-for-net-25-7/>

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On Unix or MacOS
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Usage

```bash
py ./generate_cover.py --product "GroupDocs.Total for Java" --version "25.8" --title "August 2025 release"
```

The output image is placed into `output` folder by default. Executing the example produces the following result:

![GroupDocs.Total for Java 25.7 Cover Image](./docs/groupdocs-total-for-java-25-8.png)
