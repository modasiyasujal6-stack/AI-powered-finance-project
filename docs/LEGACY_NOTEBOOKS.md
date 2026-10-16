# Exploratory notebooks

The uploaded folder contained exploratory Jupyter notebooks, notebook checkpoints, an untitled notebook, machine-specific Windows paths, and duplicate older implementations of the SQL validation/reporting logic. Those files were intentionally left out of the clean release so that the maintained Python modules are the single source of truth and old, weaker SQL guards are not accidentally run. The maintained entry points are `main.py`, `app.py`, and `python -m reports.report_generator`.
