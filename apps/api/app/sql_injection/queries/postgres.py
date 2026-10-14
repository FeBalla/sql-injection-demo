"""The INSERT this demo is about, on Postgres: concatenated vs parameterized.

WARNING: the concatenated version is INTENTIONALLY VULNERABLE to SQL injection. It exists only to
demonstrate the attack. Never copy it into real code; use the parameterized version.
"""

from sqlalchemy import Connection, CursorResult, text

from ..models import CustomerIn

# Vulnerable: the values become part of the SQL text. ----------------------------------------

CONCATENATED_INSERT = """INSERT INTO customers (name, email, country, plan)
VALUES (
  '{name}',
  '{email}',
  '{country}',
  '{plan}'
);"""


def build_concatenated_insert(customer: CustomerIn) -> str:
    """INTENTIONALLY VULNERABLE: pastes user input into the SQL text."""
    return CONCATENATED_INSERT.format(**customer.model_dump())


def insert_customer_concatenated(conn: Connection, customer: CustomerIn) -> CursorResult:
    """Postgres parses the values as SQL: a quote ends the string, a ``;`` starts a statement."""
    return conn.exec_driver_sql(build_concatenated_insert(customer))


# Safe: the SQL text is fixed, the values travel separately. ----------------------------------

PARAMETERIZED_INSERT = text("""INSERT INTO customers (name, email, country, plan)
VALUES (:name, :email, :country, :plan);""")


def insert_customer_parameterized(conn: Connection, customer: CustomerIn) -> CursorResult:
    """Postgres receives ``$1..$4`` plus the values, which are never parsed as SQL."""
    return conn.execute(PARAMETERIZED_INSERT, customer.model_dump())
