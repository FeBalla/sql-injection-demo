"""Demo rows loaded on startup (when the table is empty) and on reset. Ids are 1..12 in order."""

from .schemas import CustomerIn

SEED_ROWS: tuple[CustomerIn, ...] = tuple(
    CustomerIn(name=name, email=email, country=country, plan=plan)
    for name, email, country, plan in (
        ("Camila Fuentes", "cfuentes@example.cl", "CL", "free"),
        ("Diego Araya", "daraya@example.cl", "CL", "pro"),
        ("Lucía Méndez", "lmendez@example.pe", "PE", "free"),
        ("Tomás Ríos", "trios@example.co", "CO", "team"),
        ("Valentina Soto", "vsoto@example.cl", "CL", "pro"),
        ("Mateo Hernández", "mhernandez@example.mx", "MX", "team"),
        ("Sofía Gutiérrez", "sgutierrez@example.ar", "AR", "free"),
        ("Joaquín Paredes", "jparedes@example.pe", "PE", "pro"),
        ("Isabella Castro", "icastro@example.co", "CO", "free"),
        ("Benjamín Rojas", "brojas@example.cl", "CL", "team"),
        ("Renata Morales", "rmorales@example.mx", "MX", "pro"),
        ("Martín Acosta", "macosta@example.ar", "AR", "free"),
    )
)
