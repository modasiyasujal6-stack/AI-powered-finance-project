# Finance Operations Analytics & Local Finance AI Analyst

A portfolio project combining synthetic finance data generation, PostgreSQL reporting views, data-quality checks, automated Excel reporting, and a natural-language-to-SQL assistant that supports local Ollama or optional Groq API inference.

> This is a local portfolio prototype. It is not a production accounting system and should only be connected to a database containing data you are authorized to use. AI-generated results must be reviewed before business decisions.

## Features

- Generates synthetic master, sales, receivables, expense, payable, and bank-transaction data.
- Stops by default if managed tables already contain data, reducing accidental duplicate inserts.
- Requires an explicit two-flag confirmation before a reset that deletes generated table rows.
- Runs data-quality checks for missing relationships, invalid payment amounts, empty tables, and duplicate budget month/department combinations.
- Exports six PostgreSQL reporting views into a multi-sheet Excel workbook, plus a report-info sheet.
- Supports local Ollama (default model `qwen2.5:3b`) or optional Groq API (`openai/gpt-oss-20b`) to draft finance SQL from natural-language questions. Groq may be faster but requires your own API key and is subject to free-tier limits.
- Applies SQL allow-list checks and executes queries in a PostgreSQL read-only transaction.
- Keeps credentials in a local `.env` file instead of hardcoding them in Python source.

## Project layout

```text
finance_ops_project/
├── ai/finance_ai.py
├── config/config.py
├── db/connection.py
├── generators/
├── reports/report_generator.py
├── sql/bootstrap.sql              # fresh-database schema and reporting views
├── reports/output/                 # generated workbook (ignored by Git)
├── tests/
├── utils/
├── validations/validation_checks.py
├── app.py                          # Streamlit UI
├── main.py                         # data + validation + report pipeline
├── requirements.txt
├── .env.example
└── README.md
```

## Prerequisites

- Python 3.10 or newer
- PostgreSQL; either use the existing project schema/views or create a fresh project database with the optional bootstrap script
- Ollama installed locally and the configured model pulled (only needed for the AI UI)

The workbook export expects these views: `vw_monthly_revenue`, `vw_monthly_expenses`, `vw_budget_vs_actual`, `vw_receivables_aging`, `vw_payables_aging`, and `vw_cash_flow`. For a fresh/empty database, review `sql/bootstrap.sql` and execute it using a PostgreSQL client. **Do not run the bootstrap script against an existing database without a backup and careful review**; it includes `CREATE OR REPLACE VIEW` statements. The bootstrap SQL has not been run against a live PostgreSQL server in this build environment, so verify it on a disposable database first.

## Setup (Windows PowerShell)

1. Open a terminal in this project directory.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Create your local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

   Edit `.env` and set `DB_PASSWORD` and the correct database name. Never commit `.env`.
5. Confirm PostgreSQL is running and that the configured user can access the `finance_ops` schema.
6. Optional AI setup:

   ```powershell
   ollama pull qwen2.5:3b
   ollama serve
   ```

   If Ollama is already running as a service, you do not need to start it again.

## Run the pipeline safely

```powershell
python main.py
```

The default run only proceeds if the managed tables are empty. If they contain data, the pipeline stops and reports which tables are populated rather than appending another dataset.

To intentionally replace the generated dataset, use the following **only if you understand it permanently deletes rows** from the managed `finance_ops` tables:

```powershell
python main.py --reset --confirm-reset
```

This is destructive. Back up any important data first. Do not use it against a database with real business data.

The Excel workbook is written to `reports/output/finance_operations_report.xlsx`.

## Configure the AI provider

The default `LLM_PROVIDER=ollama` keeps prompts on your machine. To use Groq, create an API key in your own Groq Console, then set these values in your private `.env` file:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_private_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Do not commit `.env` or share the key. When using Groq, the natural-language question and schema context included in the prompt are sent to Groq's API; do not connect sensitive production data. Groq's free-tier access has rate limits and model availability can change. To return to local inference, set `LLM_PROVIDER=ollama`.

## Run the AI interface

With PostgreSQL running and the configured AI provider available (Ollama for local mode, or internet access and a valid Groq API key for Groq mode):

```powershell
streamlit run app.py
```

The app submits a natural-language question, generates SQL using the configured model provider, checks the query against an allow-list of reporting views, and runs it in a read-only transaction. SQL validation is defense in depth, not a replacement for a least-privilege database user. For safer deployments, configure a dedicated PostgreSQL user that has `SELECT` privileges only on the approved views and no write permissions on base tables.

## Tests

Run unit tests that do not require PostgreSQL or Ollama:

```powershell
python -m unittest discover -s tests -v
```

Compile-check Python files:

```powershell
python -m compileall -q .
```

Database integration tests require your own local PostgreSQL instance and are not run automatically by the unit-test suite.

## Scheduling (optional)

After the pipeline has been verified locally, Windows Task Scheduler can run `python.exe` with the argument `main.py` from the project directory. The default safety check prevents a scheduled run from appending to populated tables. For recurring reporting on a persistent dataset, schedule the report-only command `python -m reports.report_generator` from the project directory. This exports the current views without generating new data; do not schedule the destructive reset option.

## Known limitations

- The pipeline generates synthetic data; it is not connected to a live ERP or bank feed.
- The optional bootstrap SQL is provided for a fresh database, but it must be verified against PostgreSQL before use.
- AI SQL quality depends on the local model and the actual database view definitions. Review query outputs for correctness.
- This package has been source-reviewed and unit-tested in an isolated environment. A full PostgreSQL/Ollama integration run must be completed on the target machine because this environment has no access to the user's local database or Ollama service.
