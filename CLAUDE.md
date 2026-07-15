# dataqual — Project Context

## Overview
CLI tool for auditing CSV/Excel/PostgreSQL datasets — detects missing
values, duplicates, type mismatches, and outliers. Outputs report to
terminal (Rich), HTML, or JSON.

## Tech Stack
- Python 3.11+
- Typer (CLI framework)
- Pandas (data processing)
- Rich (terminal UI)
- PyYAML (config)
- pytest (testing)

## Commands
- Run: `python -m dataqual check --file sample.csv`
- Run with report: `python -m dataqual check --file sample.csv --report html`
- Compare: `python -m dataqual compare --file1 old.csv --file2 new.csv`
- Test: `pytest`
- Lint: `ruff check .`

## Project Structure
```
dataqual/
├── dataqual/
│   ├── cli.py          # Typer commands
│   ├── checks/         # missing.py, duplicates.py, outliers.py, types.py
│   ├── readers/         # CSV, Excel, PostgreSQL loaders
│   ├── report/          # html_report.py, json_report.py
│   └── config.py        # YAML parser
├── tests/
├── pyproject.toml
└── README.md
```

## Conventions
- One check type = one module in checks/
- All CLI commands live in cli.py, logic delegated to checks/ and report/
- Config values (thresholds, rules) go through config.py, never hardcoded
- Every new check needs a matching test in tests/

## Milestones
- **M1** — CLI skeleton + CSV loader + missing value check + Rich terminal output (Must)
- **M2** — Duplicate row detection + type mismatch detection (Must)
- **M3** — Outlier detection (IQR) + HTML report export (Should)
- **M4** — JSON report export + YAML config support (Should)
- **M5** — Excel/PostgreSQL support + compare mode (Could)

## Current Milestone
All five milestones are complete (as of 2026-07-15):
- **M1** ✅ CLI skeleton, CSV loader, missing value check, Rich terminal output
- **M2** ✅ Duplicate row detection (full-row + `--keys`), type mismatch detection
- **M3** ✅ IQR outlier detection, self-contained HTML report export
- **M4** ✅ JSON report export, YAML config (`--config`) with threshold overrides
- **M5** ✅ Excel (`--sheet`) + PostgreSQL (`--db-url`/`--table`/`--query`) sources, compare mode

Final feature set: CSV/Excel/PostgreSQL sources · missing/duplicate/type/outlier
checks · terminal/HTML/JSON reports · YAML config · compare mode (key-based or
positional diff).
