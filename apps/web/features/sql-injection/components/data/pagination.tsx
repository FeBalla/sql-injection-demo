import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

import { PAGE_SIZE } from "@/features/sql-injection/api/endpoints";

type PaginationProps = {
  page: number;
  pageCount: number;
  total: number;
  onPageChange: (page: number) => void;
};

/** "Rows 1–5 of 12" with previous / next page buttons. */
export function Pagination({
  page,
  pageCount,
  total,
  onPageChange,
}: PaginationProps) {
  const shownPage = Math.min(page, pageCount);
  const first = total === 0 ? 0 : (shownPage - 1) * PAGE_SIZE + 1;
  const last = Math.min(shownPage * PAGE_SIZE, total);
  const range = total === 0 ? "No rows" : `${first}–${last} of ${total}`;

  return (
    <nav
      aria-label="Table pages"
      className="flex items-center justify-between border-t border-divider py-1 pr-2 pl-4 md:border-t-0 md:py-2 md:pr-3 md:pl-5"
    >
      <span className="text-[13px] text-muted-foreground" aria-live="polite">
        <span className="hidden md:inline">{total > 0 && "Rows "}</span>
        {range}
      </span>
      <div className="flex gap-1">
        <PageButton
          label="Previous page"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft aria-hidden="true" />
        </PageButton>
        <PageButton
          label="Next page"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight aria-hidden="true" />
        </PageButton>
      </div>
    </nav>
  );
}

function PageButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex size-11 items-center justify-center rounded-md text-foreground transition-colors hover:bg-surface-subtle focus-visible:outline-2 disabled:cursor-default disabled:text-muted-foreground disabled:opacity-60 disabled:hover:bg-transparent [&_svg]:size-[18px]"
    >
      {children}
    </button>
  );
}
