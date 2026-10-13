"use client";

import { LoaderCircle, Shield, TriangleAlert, X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerTitle,
} from "@/components/ui/drawer";
import { useMediaQuery } from "@/hooks/use-media-query";
import { useScrollFade } from "@/hooks/use-scroll-fade";
import { cn } from "@/lib/utils";

import { joinList, plural, quotedPlaceholders } from "../statement-copy";
import type { DatabaseInfo, StatementPreview } from "../types";
import { CodeLines } from "./code-lines";
import { CopyButton } from "./copy-button";

type ConfirmInsertProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  statement: StatementPreview | null;
  database: DatabaseInfo;
  running: boolean;
  onConfirm: () => void;
};

const TITLE = "Run this insert?";
const DESCRIPTION =
  "Review the exact statement before it is sent to the database.";

/** Confirmation with the exact statement: a dialog on wide screens, a bottom sheet on narrow ones. */
export function ConfirmInsert({
  open,
  onOpenChange,
  statement,
  database,
  running,
  onConfirm,
}: ConfirmInsertProps) {
  const isDesktop = useMediaQuery("(min-width: 768px)", true);

  // Keep the dialog open while the insert is running.
  function handleOpenChange(next: boolean) {
    if (!running) onOpenChange(next);
  }

  const runButton = (
    <Button
      type="button"
      onClick={onConfirm}
      disabled={running}
      className="h-12 flex-[2] rounded-lg px-[22px] text-[15px] hover:bg-primary/85 md:h-11 md:flex-none md:rounded-md md:text-sm"
    >
      {running && <LoaderCircle aria-hidden="true" className="animate-spin" />}
      {running ? "Running…" : "Run insert"}
    </Button>
  );
  const cancelButton = (
    <Button
      type="button"
      variant="outline"
      disabled={running}
      className="h-12 flex-1 rounded-lg border-input bg-card px-5 text-[15px] hover:bg-surface-subtle md:h-11 md:flex-none md:rounded-md md:text-sm"
    >
      Cancel
    </Button>
  );
  const closeIcon = (
    <Button
      type="button"
      variant="ghost"
      aria-label="Close"
      disabled={running}
      className="size-11 flex-none rounded-lg text-muted-foreground hover:bg-surface-subtle [&_svg]:size-[18px]"
    >
      <X aria-hidden="true" />
    </Button>
  );

  if (isDesktop) {
    return (
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          showCloseButton={false}
          className="flex max-h-[calc(100dvh-2rem)] max-w-[680px] flex-col gap-0 overflow-y-auto rounded-2xl bg-card p-0 shadow-[0_24px_64px_rgba(0,0,0,.24)] ring-0 sm:max-w-[680px]"
        >
          <div className="flex items-start justify-between gap-4 px-6 pt-[22px] pb-[18px]">
            <div className="flex flex-col gap-2.5">
              <DialogTitle className="text-lg leading-tight font-semibold">
                {TITLE}
              </DialogTitle>
              <DialogDescription className="sr-only">
                {DESCRIPTION}
              </DialogDescription>
              {statement && (
                <StatementChips statement={statement} database={database} />
              )}
            </div>
            <DialogClose asChild>{closeIcon}</DialogClose>
          </div>
          {statement && (
            <div className="flex flex-col gap-4 px-6">
              <ConfirmBody statement={statement} compact={false} />
            </div>
          )}
          <div className="flex justify-end gap-2.5 px-6 pt-5 pb-6">
            <DialogClose asChild>{cancelButton}</DialogClose>
            {runButton}
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Drawer open={open} onOpenChange={handleOpenChange}>
      <DrawerContent className="bg-card data-[vaul-drawer-direction=bottom]:max-h-[90dvh] data-[vaul-drawer-direction=bottom]:rounded-t-[20px] data-[vaul-drawer-direction=bottom]:border-t-0">
        <div className="flex items-center justify-between gap-3 pt-1.5 pr-2 pl-4">
          <DrawerTitle className="text-lg font-semibold">{TITLE}</DrawerTitle>
          <DrawerDescription className="sr-only">
            {DESCRIPTION}
          </DrawerDescription>
          <DrawerClose asChild>{closeIcon}</DrawerClose>
        </div>
        {statement && (
          <div className="flex flex-col gap-3.5 overflow-y-auto px-4 pt-2 pb-4">
            <StatementChips statement={statement} database={database} compact />
            <ConfirmBody statement={statement} compact />
          </div>
        )}
        <div className="flex gap-2.5 border-t border-divider px-4 pt-3 pb-[calc(24px+env(safe-area-inset-bottom))]">
          <DrawerClose asChild>{cancelButton}</DrawerClose>
          {runButton}
        </div>
      </DrawerContent>
    </Drawer>
  );
}

function Chip({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "info" | "warning";
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-[26px] items-center gap-1.5 rounded-sm px-2.5 font-mono text-xs [&_svg]:size-[13px] [&_svg]:stroke-[2.2]",
        tone === "neutral" && "bg-tag text-tag-foreground",
        tone === "info" && "bg-info-soft text-info-strong",
        tone === "warning" && "bg-warning-soft text-warning-strong",
      )}
    >
      {children}
    </span>
  );
}

function StatementChips({
  statement,
  database,
  compact = false,
}: {
  statement: StatementPreview;
  database: DatabaseInfo;
  compact?: boolean;
}) {
  const count = statement.statement_count;
  return (
    <div className="flex flex-wrap gap-1.5 md:gap-2">
      <Chip>
        {compact ? database.label : `${database.label} · ${database.table}`}
      </Chip>
      <Chip tone={count > 1 ? "warning" : "neutral"}>
        {plural(count, "statement")}
      </Chip>
      {statement.parameterized ? (
        <Chip tone="info">
          <Shield aria-hidden="true" />
          Parameterized
        </Chip>
      ) : (
        <Chip tone="warning">
          <TriangleAlert aria-hidden="true" />
          Concatenated
        </Chip>
      )}
    </div>
  );
}

function ConfirmBody({
  statement,
  compact,
}: {
  statement: StatementPreview;
  compact: boolean;
}) {
  const codeRef = useScrollFade<HTMLDivElement>();
  return (
    <>
      <div className="overflow-hidden rounded-xl bg-code md:rounded-lg">
        <div className="flex items-center justify-between border-b border-code-border py-1 pr-1 pl-3 md:py-2 md:pr-2 md:pl-3.5">
          <span className="text-xs tracking-[.04em] text-code-muted uppercase">
            {compact ? "Statement" : "Statement sent to the database"}
          </span>
          <CopyButton
            text={statement.sql}
            className="h-11 px-3 text-[13px] md:h-8 md:px-2.5 md:text-xs"
          />
        </div>
        <div
          ref={codeRef}
          className="max-h-[200px] overflow-auto py-2.5 data-more:[mask-image:linear-gradient(to_right,#000_calc(100%-2rem),transparent)] md:py-3"
        >
          <CodeLines lines={statement.lines} gutter="dialog" />
        </div>
      </div>

      {statement.parameterized && statement.params.length > 0 && (
        <BoundParamsTable statement={statement} compact={compact} />
      )}

      <ConfirmNote statement={statement} />
    </>
  );
}

function BoundParamsTable({
  statement,
  compact,
}: {
  statement: StatementPreview;
  compact: boolean;
}) {
  const cell = compact ? "px-3 py-2.5" : "px-3.5 py-2.5";
  return (
    <div className="overflow-hidden rounded-xl border md:rounded-lg">
      <table className="w-full table-fixed font-mono text-[13px]">
        <caption
          className={cn(
            "bg-surface-subtle text-left font-sans text-xs tracking-[.04em] text-muted-foreground uppercase",
            compact ? "px-3 py-2.5" : "px-3.5 py-2.5",
          )}
        >
          Bound parameters
        </caption>
        <colgroup>
          <col className={compact ? "w-[52px]" : "w-[70px]"} />
          <col className={compact ? "w-[82px]" : "w-[132px]"} />
          {!compact && <col className="w-[76px]" />}
          <col />
        </colgroup>
        <thead className={cn(compact ? "sr-only" : "bg-surface-subtle")}>
          <tr className="border-t border-divider text-left text-xs text-muted-foreground">
            <th scope="col" className={cn("font-normal", cell)}>
              param
            </th>
            <th scope="col" className={cn("font-normal", cell)}>
              column
            </th>
            {!compact && (
              <th scope="col" className={cn("font-normal", cell)}>
                type
              </th>
            )}
            <th scope="col" className={cn("font-normal", cell)}>
              value
            </th>
          </tr>
        </thead>
        <tbody>
          {statement.params.map((param) => (
            <tr key={param.placeholder} className="border-t border-divider">
              <td className={cn("font-medium text-param", cell)}>
                {param.placeholder}
              </td>
              <td className={cn(compact && "text-muted-foreground", cell)}>
                {param.column}
              </td>
              {!compact && (
                <td className={cn("text-muted-foreground", cell)}>
                  {param.type}
                </td>
              )}
              <td className={cn("[overflow-wrap:anywhere]", cell)}>
                {param.value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ConfirmNote({ statement }: { statement: StatementPreview }) {
  if (statement.parameterized) {
    const quoted = quotedPlaceholders(statement);
    if (quoted.length === 0) {
      return <Note>Values are sent separately and stored as data.</Note>;
    }
    const quoteCount = statement.params.reduce(
      (total, param) => total + param.value.split("'").length - 1,
      0,
    );
    const many = quoteCount > 1;
    return (
      <Note>
        {many ? "The quotes" : "The apostrophe"} in{" "}
        {quoted.map((placeholder, i) => (
          <span key={placeholder}>
            {i > 0 && (i === quoted.length - 1 ? " and " : ", ")}
            <span className="font-mono text-foreground">{placeholder}</span>
          </span>
        ))}{" "}
        {many ? "are" : "is"} stored as data.{" "}
        {many ? "They never become" : "It never becomes"} part of the SQL.
      </Note>
    );
  }

  const escaped = statement.escaped_fields;
  if (escaped.length === 0) {
    return <Note>Values are pasted into the SQL text as they are.</Note>;
  }
  const count = statement.statement_count;
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-warning-border bg-warning-soft px-3.5 py-3 text-[13px] leading-normal text-warning-strong">
      <TriangleAlert aria-hidden="true" className="mt-px size-4 flex-none" />
      <p>
        Input in <span className="font-mono">{joinList(escaped)}</span> escapes
        its string literal and becomes SQL.{" "}
        {count > 1
          ? `The database will receive ${count} statements in one request.`
          : "The database receives 1 statement with that text as part of its code."}
      </p>
    </div>
  );
}

function Note({ children }: { children: ReactNode }) {
  return (
    <p className="text-[13px] leading-normal text-muted-foreground">
      {children}
    </p>
  );
}
