# dataqual

CLI tool for auditing CSV/Excel/PostgreSQL datasets — detects missing values, duplicates, type mismatches, and outliers.

## Install

```bash
pip install -e .
```

## Check a dataset

Basic CSV check (Rich terminal report):

```bash
dataqual check --file data.csv
```

Export the report as a self-contained HTML page or JSON file
(written to `<name>_report.html` / `<name>_report.json`):

```bash
dataqual check --file data.csv --report html
dataqual check --file data.csv --report json
```

Detect duplicates by key column(s) instead of full-row equality
(rows with null keys are skipped, not treated as matching):

```bash
dataqual check --file data.csv --keys email
dataqual check --file data.csv --keys "email,phone"
```

Override alert thresholds with a YAML config
(see [dataqual.config.yaml](dataqual.config.yaml) for a commented example):

```bash
dataqual check --file data.csv --config dataqual.config.yaml
```

Load from Excel — `--sheet` takes a name or zero-based index, default first sheet:

```bash
dataqual check --file data.xlsx
dataqual check --file data.xlsx --sheet inventory
```

## Check a PostgreSQL table or query

Use `--db-url` instead of `--file`, plus exactly one of `--table` or `--query`:

```bash
dataqual check --db-url postgresql://user:pass@host:5432/db --table public.users
dataqual check --db-url postgresql://user:pass@host:5432/db --query "SELECT * FROM users WHERE active"
```

## Compare two datasets

Diff two files (CSV or Excel) — rows added, removed, and changed, with
old/new values per column. `--keys` identifies "the same row" across both
files and is strongly recommended; without it rows are matched by position:

```bash
dataqual compare --file1 old.csv --file2 new.csv --keys id
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```
