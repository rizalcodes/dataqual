# 🔍 dataqual — Dataset Quality Auditing CLI

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![Typer](https://img.shields.io/badge/Typer-CLI-000000?style=flat-square)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white)
![Rich](https://img.shields.io/badge/Rich-Terminal_UI-FF6E00?style=flat-square)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-PostgreSQL-D71F00?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-64_passing-brightgreen?style=flat-square)

---

## ❓ Problem

Anyone who's opened a "clean" CSV knows it rarely is. Missing values, duplicate rows, mismatched types, and outliers hide in plain sight — and finding them usually means writing the same ad-hoc `df.isnull().sum()` and `df.duplicated()` checks over and over in a notebook, one dataset at a time.

There's no quick, repeatable way to audit a dataset — CSV, Excel, or a live database table — and get a clear, shareable answer to "is this data actually usable?"

---

## 💡 Solution

A CLI tool that audits any dataset in one command and tells you exactly what's wrong with it:

- **Point it at a file or a database** — CSV, Excel, or a PostgreSQL table/query
- **Four checks, every time** — missing values, duplicates, type mismatches, outliers
- **Three ways to see the result** — color-coded terminal report, self-contained HTML file, or structured JSON for pipelines
- **Tune what counts as "bad"** — YAML config overrides the alert thresholds per check
- **Diff two datasets** — see exactly what rows were added, removed, or changed between versions

---

## ✨ Features

- 🕳️ **Missing Value Detection** — count and % per column, color-coded by severity
- 🧬 **Duplicate Row Detection** — full-row or key-column based (`--keys email`), with null-safe matching
- 🔀 **Type Mismatch Detection** — flags values that don't match a column's inferred type (numeric, date, string), with example offenders shown
- 📊 **Outlier Detection (IQR)** — flags statistical outliers per numeric column with the expected range
- 🎨 **Rich Terminal Reports** — color-coded tables (green/yellow/red) straight in your shell
- 🌐 **Self-Contained HTML Reports** — one offline HTML file per audit, safe to share, no external dependencies
- 🧾 **JSON Reports** — structured output for downstream tooling and pipelines
- ⚙️ **Configurable Thresholds** — override alert sensitivity per check via `--config config.yaml`
- 🗂️ **Multi-Source Input** — CSV, Excel (`.xlsx`, multi-sheet), or PostgreSQL (`--db-url`)
- 🔄 **Compare Mode** — diff two datasets by key or row position, see old/new values for every change

---

## 🛠️ Tech Stack

| Layer | Tool | Purpose |
|---|---|---|
| CLI Framework | Typer | Command parsing, options, help text |
| Data Processing | Pandas | Loading, checks, comparisons |
| Terminal UI | Rich | Color-coded tables in the shell |
| Excel Support | openpyxl | Reading `.xlsx` workbooks |
| Database | SQLAlchemy + psycopg2 | PostgreSQL connection and querying |
| Config | PyYAML | Threshold override files |
| Testing | pytest | 64 tests across checks, readers, reports, and CLI |

---

## 📡 Commands

### Audit a dataset

```bash
dataqual check --file data.csv
```

| Flag | Description |
|---|---|
| `--report terminal\|html\|json` | Output format (default: terminal) |
| `--keys email,phone` | Match duplicates by key column(s) instead of full row |
| `--config rules.yaml` | Override alert thresholds |
| `--sheet name_or_index` | Excel sheet to read (default: first) |
| `--db-url ...` | Connect to PostgreSQL instead of a file |
| `--table name` / `--query "SQL"` | What to load from the database (pick one) |

### Compare two datasets

```bash
dataqual compare --file1 old.csv --file2 new.csv --keys id
```

Reports rows added, removed, and changed — with the specific columns and old/new values for every change.

---

## 📁 Project Structure

```
dataqual/
├── dataqual/
│   ├── cli.py              # Typer app — check & compare commands
│   ├── checks/              # missing, duplicates, types, outliers, compare
│   ├── readers/              # csv, excel, postgres loaders
│   ├── report/                # terminal, html, json renderers
│   └── config.py               # threshold defaults + YAML loading
├── tests/                       # 64 tests
├── dataqual.config.yaml          # sample threshold override file
└── pyproject.toml
```

---

## ⚡ Quick Start

### 1. Clone & set up environment

```bash
git clone https://github.com/rizalcodes/dataqual.git
cd dataqual

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -e .
```

### 2. Run it

```bash
dataqual check --file data.csv
```

### 3. (For development)

```bash
pip install -e ".[dev]"
pytest
```

---

## 👤 Author

**Rizal**

[![Portfolio](https://img.shields.io/badge/Portfolio-rizalcodes.github.io-0A66C2?style=flat-square)](https://rizalcodes.github.io)
[![GitHub](https://img.shields.io/badge/GitHub-rizalcodes-181717?style=flat-square&logo=github)](https://github.com/rizalcodes)
[![Twitter/X](https://img.shields.io/badge/X-@rizalcodes_-000000?style=flat-square&logo=x)](https://x.com/rizalcodes_)

---

*Built with Typer, Pandas, and the belief that "clean data" is a claim, not a fact — until you've checked.*
