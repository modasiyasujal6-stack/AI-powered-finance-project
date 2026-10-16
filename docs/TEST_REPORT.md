# Build and test report

## Automated checks completed in the isolated build environment

- Python source compilation (`compileall`): passed.
- Unit tests: 24 passed, 0 failed.
- SQL guardrail tests: approved SELECTs accepted; multiple statements, DML, unapproved views, unqualified tables, system catalog access, and unknown/side-effecting functions rejected.
- Pipeline safety tests: empty tables allow a run; populated tables stop the pipeline with a clear error.
- Excel report generator test: workbook successfully created with six report sheets plus `Report Info` using a mocked database result source.
- Credential/source scan: hardcoded database password removed from maintained Python source; `.env` excluded from Git.

## Not verified in this environment

- Live PostgreSQL connection, actual schema constraints, view definitions, and full data generation pipeline.
- The optional `sql/bootstrap.sql` against a real PostgreSQL server.
- Ollama availability, installed model, generated SQL quality, and Streamlit browser interaction.
- Windows Task Scheduler execution on the user's machine.

These require the target machine's PostgreSQL and Ollama services. Do not describe them as fully integration-tested until completed locally.
