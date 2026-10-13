import type { StatementPreview } from "@/features/sql-injection/model/types";

/** The bound values under the preview; the type column is hidden on narrow screens. */
export function BoundParamsList({ preview }: { preview: StatementPreview }) {
  return (
    <div className="mx-4 mb-3 overflow-hidden rounded-md border border-code-border md:mx-5 md:mb-4">
      <h3 className="hidden bg-code-header px-3 py-2 text-xs font-normal tracking-[.04em] text-code-muted uppercase md:block">
        Bound parameters
      </h3>
      <dl className="divide-y divide-code-divider font-mono text-[13px] md:border-t md:border-code-divider">
        {preview.params.map((param) => (
          <div
            key={param.placeholder}
            className="grid grid-cols-[72px_minmax(0,1fr)] gap-2.5 px-3 py-2 md:grid-cols-[72px_70px_minmax(0,1fr)] md:gap-3"
          >
            <dt className="text-code-param">{param.placeholder}</dt>
            <dd className="hidden text-code-muted md:block">{param.type}</dd>
            <dd
              className="truncate text-code-string"
              title={param.value || undefined}
            >
              {param.value}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
