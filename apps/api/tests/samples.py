"""Demo inputs from the shared contract."""

from app.modules.sql_injection.schemas import CustomerIn

APOSTROPHE = CustomerIn(
    name="Bernardo O'Higgins", email="bohiggins@example.cl", country="CL", plan="pro"
)


def malicious(table: str) -> CustomerIn:
    """The malicious example: deletes every row of ``table``."""
    return CustomerIn(
        name="Mallory",
        email="mallory@example.com",
        country="CL",
        plan=f"free'); DELETE FROM {table} WHERE TRUE; SELECT ('",
    )
