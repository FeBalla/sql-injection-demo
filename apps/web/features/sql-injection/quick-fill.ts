import type { CustomerRow } from "./types";

export const EMPTY_ROW: CustomerRow = {
  name: "",
  email: "",
  country: "",
  plan: "",
};

/**
 * A legitimate name with an apostrophe. Concatenated into the SQL, the quote
 * closes the string literal early and the INSERT fails with a syntax error.
 * As a bound parameter it is stored as-is.
 */
export const APOSTROPHE_EDGE_CASE: CustomerRow = {
  name: "Bernardo O'Higgins",
  email: "bohiggins@example.cl",
  country: "CL",
  plan: "pro",
};

/**
 * A crafted `plan` that closes the string literal and the INSERT, deletes every
 * row of the demo table, and opens a harmless `SELECT ('` that swallows the
 * template's trailing `'\n);`. Concatenated, the database runs 3 statements and
 * the table ends up empty. Parameterized, the value is stored literally.
 *
 * @param table Table reference of the selected database (DatabaseInfo.table).
 */
export function maliciousExample(table: string): CustomerRow {
  return {
    name: "Mallory",
    email: "mallory@example.com",
    country: "CL",
    plan: `free'); DELETE FROM ${table} WHERE TRUE; SELECT ('`,
  };
}

/** Plausible rows for "Random valid row". None of them contains a quote. */
export const VALID_ROWS: readonly CustomerRow[] = [
  {
    name: "Ana Rojas",
    email: "arojas@example.cl",
    country: "CL",
    plan: "free",
  },
  {
    name: "Martín Gómez",
    email: "mgomez@example.ar",
    country: "AR",
    plan: "pro",
  },
  {
    name: "Sofía Herrera",
    email: "sherrera@example.mx",
    country: "MX",
    plan: "team",
  },
  {
    name: "Joaquín Silva",
    email: "jsilva@example.uy",
    country: "UY",
    plan: "free",
  },
  {
    name: "Isabela Costa",
    email: "icosta@example.br",
    country: "BR",
    plan: "pro",
  },
  {
    name: "Mateo Vargas",
    email: "mvargas@example.pe",
    country: "PE",
    plan: "team",
  },
  {
    name: "Renata Castillo",
    email: "rcastillo@example.co",
    country: "CO",
    plan: "pro",
  },
  {
    name: "Felipe Navarro",
    email: "fnavarro@example.cl",
    country: "CL",
    plan: "free",
  },
];

/** A random row from VALID_ROWS, different from `current` when possible. */
export function randomValidRow(current?: CustomerRow): CustomerRow {
  const candidates = VALID_ROWS.filter((row) => row.email !== current?.email);
  return candidates[Math.floor(Math.random() * candidates.length)];
}
