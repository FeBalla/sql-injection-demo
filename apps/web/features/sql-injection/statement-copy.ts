import type { StatementPreview } from "./types";

/** "a", "a and b", "a, b and c". */
export function joinList(items: readonly string[]): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

export function plural(count: number, singular: string, pluralForm?: string) {
  return `${count} ${count === 1 ? singular : (pluralForm ?? `${singular}s`)}`;
}

/** "$1–$4" for numbered placeholders, "@name, @email, @country and @plan" otherwise. */
function placeholderList(preview: StatementPreview): string {
  const placeholders = preview.params.map((param) => param.placeholder);
  if (placeholders.length > 1 && placeholders.every((p) => p.startsWith("$"))) {
    return `${placeholders[0]}–${placeholders[placeholders.length - 1]}`;
  }
  return joinList(placeholders);
}

export type StatusCopy = {
  tone: "safe" | "unsafe";
  title: string;
  body: string;
  /** Shorter title for narrow screens. */
  shortTitle: string;
  /** Shorter body for narrow screens; falls back to `body`. */
  shortBody: string;
};

/** Copy for the status box under the query preview. */
export function statusCopy(preview: StatementPreview): StatusCopy {
  if (preview.parameterized) {
    return {
      tone: "safe",
      title: "Values travel separately from the SQL",
      body: `The database parses the statement first, then binds ${placeholderList(preview)} as plain data. Input values can no longer change the query.`,
      shortTitle: "Values travel separately",
      shortBody: "The query is parsed first; values are bound as plain data.",
    };
  }

  const title = "Your input is part of the SQL text";
  const shortTitle = "Your input is part of the SQL";
  const field = preview.escaped_fields[0];

  if (field && preview.statement_count > 1) {
    const body = `The value in ${field} breaks out of its string literal and turns this into ${preview.statement_count} statements, all sent to the database in one request.`;
    return { tone: "unsafe", title, body, shortTitle, shortBody: body };
  }
  if (field) {
    return {
      tone: "unsafe",
      title,
      body: `The value in ${field} breaks out of its string literal, so it is now part of the SQL. A crafted value could rewrite the statement or add another one.`,
      shortTitle,
      shortBody: `The value in ${field} breaks out of its string and is now SQL.`,
    };
  }
  const body =
    "These values are pasted into the SQL text as they are. A single quote in any of them would be enough to change the query.";
  return { tone: "unsafe", title, body, shortTitle, shortBody: body };
}

/** Placeholders whose bound value contains a quote, e.g. ["$1"]. */
export function quotedPlaceholders(preview: StatementPreview): string[] {
  return preview.params
    .filter((param) => param.value.includes("'"))
    .map((param) => param.placeholder);
}
