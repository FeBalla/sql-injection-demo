import { LoaderCircle } from "lucide-react";

import { Button } from "@/components/ui/button";

import { INSERT_FORM_ID } from "./insert-form";

/** Sticky Clear / Review & insert bar on narrow screens. */
export function MobileActionBar({
  onClear,
  reviewing,
}: {
  onClear: () => void;
  reviewing: boolean;
}) {
  return (
    <div className="sticky bottom-0 z-10 flex gap-2.5 border-t bg-card px-4 pt-3 pb-[calc(20px+env(safe-area-inset-bottom))] md:hidden">
      <Button
        type="button"
        variant="outline"
        onClick={onClear}
        className="h-12 flex-1 rounded-lg border-input bg-card text-[15px] hover:bg-surface-subtle"
      >
        Clear
      </Button>
      <Button
        type="submit"
        form={INSERT_FORM_ID}
        disabled={reviewing}
        className="h-12 flex-[2] rounded-lg text-[15px] hover:bg-primary/85"
      >
        {reviewing && (
          <LoaderCircle aria-hidden="true" className="animate-spin" />
        )}
        Review &amp; insert
      </Button>
    </div>
  );
}
