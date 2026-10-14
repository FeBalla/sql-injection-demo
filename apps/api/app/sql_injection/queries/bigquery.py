"""The INSERT this demo is about, on BigQuery: concatenated vs parameterized.

WARNING: the concatenated version is INTENTIONALLY VULNERABLE to SQL injection. It exists only to
demonstrate the attack. Never copy it into real code; use the parameterized version.

``table`` is the demo table from the settings (``<dataset>.customers``), never user input.
BigQuery has no auto-increment, so the statement computes the next id itself.
"""

from google.cloud import bigquery

from ..models import CustomerIn

# Vulnerable: the values become part of the SQL text. ----------------------------------------

CONCATENATED_INSERT = """INSERT INTO `{table}` (id, name, email, country, plan)
VALUES (
  (SELECT COALESCE(MAX(id), 0) + 1 FROM `{table}`),
  '{name}',
  '{email}',
  '{country}',
  '{plan}'
);"""


def build_concatenated_insert(table: str, customer: CustomerIn) -> str:
    """INTENTIONALLY VULNERABLE: pastes user input into the SQL text."""
    return CONCATENATED_INSERT.format(table=table, **customer.model_dump())


def insert_customer_concatenated(
    client: bigquery.Client, table: str, customer: CustomerIn
) -> bigquery.QueryJob:
    """BigQuery parses the values as SQL: a quote ends the string, a ``;`` starts a statement."""
    return client.query(build_concatenated_insert(table, customer))


# Safe: the SQL text is fixed, the values travel separately. ----------------------------------

PARAMETERIZED_INSERT = """INSERT INTO `{table}` (id, name, email, country, plan)
VALUES (
  (SELECT COALESCE(MAX(id), 0) + 1 FROM `{table}`),
  @name, @email, @country, @plan
);"""


def build_parameterized_insert(table: str) -> str:
    return PARAMETERIZED_INSERT.format(table=table)


def query_parameters(customer: CustomerIn) -> list[bigquery.ScalarQueryParameter]:
    return [
        bigquery.ScalarQueryParameter(column, "STRING", value)
        for column, value in customer.model_dump().items()
    ]


def insert_customer_parameterized(
    client: bigquery.Client, table: str, customer: CustomerIn
) -> bigquery.QueryJob:
    """BigQuery receives ``@name``... plus the values, which are never parsed as SQL."""
    job_config = bigquery.QueryJobConfig(query_parameters=query_parameters(customer))
    return client.query(build_parameterized_insert(table), job_config=job_config)
