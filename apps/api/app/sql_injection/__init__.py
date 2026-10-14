"""SQL injection demo: the same INSERT, concatenated vs parameterized, on Postgres and BigQuery.

Layers, from the HTTP edge inwards:

* ``api``: endpoints, request/response models and dependencies (no business logic),
* ``services``: the use cases (no HTTP, no SQL),
* ``queries``: the INSERT the demo is about, vulnerable and safe side by side,
* ``repositories``: every other (safe) SQL, and running the INSERT within the demo's limits,
* ``preview``: the highlighted, analyzed SQL shown before running it (no database access).
"""
