# Requirements_Extraction

### Basic idea:
Given a policy document or manual, how can we use AI to break it down to its core parts and ideas. If we can use AI to do this systematically, then we can aggregate requirements across different dimensions. For instance if we can filter for all requirements a commanding officer has across different manuals and documents or if we can filter on a certain program/system and see who has responsitility for X, Y, or Z and so on.

### Input will always be PDF:
- Current inputs include Navy Training System Plans sourced from [https://www.globalsecurity.org/military/library/policy/navy/ntsp/index.html](GlobalSecurity.org), NAVADMINS, and a few other random Navy instructions.

### Output will be JSON formatted insights:
1. Extract metadata such as `File Name/Location`, `Title`, `References`, `Summary`, `Type` (like SECNAVINST, NTSP, etc.), etc...
2. Extract requirements such as `Commanding Officers shall maintain a CMEO program` or `Aviation boatswains mates will know how to maintain system X` with specific references to who, what the requirement is, what level is it (must, shall, should, ...), timeframes, or whatever else.

### Some notes:
- Metatdata task. I expect the metadata extraction is very cleanly solved by someone smarter than us. I recommend finding a good code base or method and copying whatever you can to make it work for our documents.
- Requirements Extraction Task. I expect someone has done something very similar to this as well, but perhaps not in a nice code base for military documents. The goal is to be able to run over a large technical manual and a simply OPNAV instruction with the same code and get the unique information within the documents out in an organized way.

## Quickstart (local)

```bash
python -m pip install -e .
python run_requirements_extraction.py \
  --parsed-text-dir parsed_text \
  --metadata-dir metadata \
  --output-path requirements.jsonl
```

## Validate extraction output

```bash
python validate_requirements_jsonl.py requirements.jsonl
```

## Databricks usage notes

You do **not** need a separate repo environment to start. The recommended path is:

1. Build and upload this package as a wheel.
2. Install it as a cluster library.
3. Run a Databricks job that calls the CLI with DBFS/S3 paths.

Example job task command:

```bash
python run_requirements_extraction.py \
  --parsed-text-dir /dbfs/path/to/parsed_text \
  --metadata-dir /dbfs/path/to/metadata \
  --output-path /dbfs/path/to/requirements.jsonl
```

For production, use CI (`.github/workflows/ci.yml`) to run tests on every PR before deploying updated wheels.
