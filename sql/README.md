# Database bootstrap

`bootstrap.sql` defines the base tables and reporting views expected by the Python project for a **new, empty project database**. Review the SQL and business definitions before using it.

**Do not run this script against the existing Finance Ops database without taking a backup and reviewing the `CREATE OR REPLACE VIEW` statements.** It is not a migration script for an existing schema. The DSO/DPO and forecast views are simplified portfolio calculations, not audited accounting definitions.

The script has not been executed against a live PostgreSQL server in this build environment. Run it against a disposable local database first, then verify the expected view names and columns before connecting the pipeline.
