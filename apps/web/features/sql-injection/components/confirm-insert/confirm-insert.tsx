"use client";

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
import type {
  DatabaseInfo,
  StatementPreview,
} from "@/features/sql-injection/model/types";
import { useMediaQuery } from "@/hooks/use-media-query";

import { CancelButton, CloseButton, RunInsertButton } from "./confirm-actions";
import { ConfirmContent } from "./confirm-content";
import { StatementChips } from "./statement-chips";

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
export function ConfirmInsert(props: ConfirmInsertProps) {
  const isDesktop = useMediaQuery("(min-width: 768px)", true);

  // Keep it open while the insert is running.
  function handleOpenChange(next: boolean) {
    if (!props.running) props.onOpenChange(next);
  }

  return isDesktop ? (
    <ConfirmDialog {...props} onOpenChange={handleOpenChange} />
  ) : (
    <ConfirmSheet {...props} onOpenChange={handleOpenChange} />
  );
}

function ConfirmDialog({
  open,
  onOpenChange,
  statement,
  database,
  running,
  onConfirm,
}: ConfirmInsertProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
          <DialogClose asChild>
            <CloseButton disabled={running} />
          </DialogClose>
        </div>
        {statement && (
          <div className="flex flex-col gap-4 px-6">
            <ConfirmContent statement={statement} compact={false} />
          </div>
        )}
        <div className="flex justify-end gap-2.5 px-6 pt-5 pb-6">
          <DialogClose asChild>
            <CancelButton disabled={running} />
          </DialogClose>
          <RunInsertButton running={running} onClick={onConfirm} />
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ConfirmSheet({
  open,
  onOpenChange,
  statement,
  database,
  running,
  onConfirm,
}: ConfirmInsertProps) {
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent className="bg-card data-[vaul-drawer-direction=bottom]:max-h-[90dvh] data-[vaul-drawer-direction=bottom]:rounded-t-[20px] data-[vaul-drawer-direction=bottom]:border-t-0">
        <div className="flex items-center justify-between gap-3 pt-1.5 pr-2 pl-4">
          <DrawerTitle className="text-lg font-semibold">{TITLE}</DrawerTitle>
          <DrawerDescription className="sr-only">
            {DESCRIPTION}
          </DrawerDescription>
          <DrawerClose asChild>
            <CloseButton disabled={running} />
          </DrawerClose>
        </div>
        {statement && (
          <div className="flex flex-col gap-3.5 overflow-y-auto px-4 pt-2 pb-4">
            <StatementChips statement={statement} database={database} compact />
            <ConfirmContent statement={statement} compact />
          </div>
        )}
        <div className="flex gap-2.5 border-t border-divider px-4 pt-3 pb-[calc(24px+env(safe-area-inset-bottom))]">
          <DrawerClose asChild>
            <CancelButton disabled={running} />
          </DrawerClose>
          <RunInsertButton running={running} onClick={onConfirm} />
        </div>
      </DrawerContent>
    </Drawer>
  );
}
