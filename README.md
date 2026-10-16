# Finance Operations Analytics & AI Finance Assistant

An end-to-end portfolio project demonstrating Python-based finance data generation, PostgreSQL reporting, data-quality checks, automated Excel reporting, and an AI-assisted natural-language-to-SQL interface.

> **Portfolio prototype:** Uses synthetic finance data. It is not a production accounting system and should not be connected to sensitive business data.

## Skills demonstrated

- **Python:** modular scripts, data generation, pipeline orchestration, reporting logic.
- **SQL and PostgreSQL:** relational storage, reporting views, finance queries.
- **Pipeline safety and data quality:** validation checks and safeguards against accidental duplicate loads.
- **Excel report automation:** export data from PostgreSQL reporting views to a multi-sheet workbook.
- **AI-enabled analytics:** draft SQL from plain-English questions using local Ollama or optional Groq API.
- **SQL safety:** query validation and PostgreSQL read-only transaction execution.
- **Streamlit:** interactive interface to ask finance questions and review SQL/results.
- **Testing and version control:** unit tests, Git, and GitHub.

## Architecture

```text
Synthetic finance data
        ↓
Python generators + main.py orchestration
        ↓
PostgreSQL tables and reporting views
        ├──→ Python report generator → Excel workbook
        └──→ Streamlit app → Ollama or Groq → SQL validation
                                             ↓
                                 PostgreSQL read-only query
                                             ↓
                                        Results shown
```

## Main workflows

### Pipeline and reporting
Run `python main.py` after configuring PostgreSQL. The pipeline coordinates the project workflow, including synthetic data generation, validation, and report generation. It stops by default if managed tables already contain data to reduce accidental duplicate inserts.

### Excel automation
The report generator queries PostgreSQL reporting views and exports a multi-sheet workbook to `reports/output/finance_operations_report.xlsx`. The workbook export expects these views: `vw_monthly_revenue`, `vw_monthly_expenses`, `vw_budget_vs_actual`, `vw_receivables_aging`, `vw_payables_aging`, and `vw_cash_flow`.

Run only the report-export step with:
```powershell
python -m reports.report_generator
```

### AI finance assistant
Run `streamlit run app.py`. A user submits a finance question in plain English; the configured model drafts SQL, the application validates the query against its restrictions, and the query runs in a PostgreSQL read-only transaction. Results are displayed in the interface. AI-generated SQL and results must still be reviewed.

## Setup (Windows PowerShell)

Requirements: Python 3.10+, PostgreSQL, and either Ollama with the configured model or a Groq API key for AI features.

```powershell
git clone https://github.com/modasiyasujal6-stack/AI-powered-finance-project.git
cd AI-powered-finance-project
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your own database settings. Never commit or share `.env`.

For Groq, set these values in `.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_private_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

For local Ollama, set `LLM_PROVIDER=ollama` and install/run the configured model locally.

Prepare the PostgreSQL schema, tables, and required views. Review `sql/bootstrap.sql` and test it on a disposable database before use; do not blindly run it against an existing database.

Run:
```powershell
python main.py
streamlit run app.py
python -m unittest discover -s tests -v
```

## Safety and limitations

- Synthetic data only; no live ERP or bank feed is connected.
- The reset command permanently deletes rows from managed tables. Use `python main.py --reset --confirm-reset` only after reviewing the code and backing up important data.
- SQL validation is an additional safeguard, not a guarantee that an answer is correct. A least-privilege PostgreSQL user with SELECT access only to approved views is safer.
- In Groq mode, the prompt/question and included schema context are sent to an external API. Do not use sensitive production data.
- The optional bootstrap SQL and full clean-machine integration should be tested in the target environment.
- Windows Task Scheduler is an optional configuration; do not claim scheduled production execution unless you have configured and tested it.

## Repository

https://github.com/modasiyasujal6-stack/AI-powered-finance-project

