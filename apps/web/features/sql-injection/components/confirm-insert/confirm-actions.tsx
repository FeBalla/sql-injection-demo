import { LoaderCircle, X } from "lucide-react";
import type { ComponentProps } from "react";

import { Button } from "@/components/ui/button";

// Cancel and Close are rendered inside DialogClose / DrawerClose with
// `asChild`, so they pass the props those inject on to the button.

/** Sized as a flexible footer button on narrow screens, a compact one on wide. */
export function RunInsertButton({
  running,
  onClick,
}: {
  running: boolean;
  onClick: () => void;
}) {
  return (
    <Button
      type="button"
      onClick={onClick}
      disabled={running}
      className="h-12 flex-[2] rounded-lg px-[22px] text-[15px] hover:bg-primary/85 md:h-11 md:flex-none md:rounded-md md:text-sm"
    >
      {running && <LoaderCircle aria-hidden="true" className="animate-spin" />}
      {running ? "Running…" : "Run insert"}
    </Button>
  );
}

export function CancelButton(props: ComponentProps<"button">) {
  return (
    <Button
      {...props}
      type="button"
      variant="outline"
      className="h-12 flex-1 rounded-lg border-input bg-card px-5 text-[15px] hover:bg-surface-subtle md:h-11 md:flex-none md:rounded-md md:text-sm"
    >
      Cancel
    </Button>
  );
}

/** The × in the top corner. */
export function CloseButton(props: ComponentProps<"button">) {
  return (
    <Button
      {...props}
      type="button"
      variant="ghost"
      aria-label="Close"
      className="size-11 flex-none rounded-lg text-muted-foreground hover:bg-surface-subtle [&_svg]:size-[18px]"
    >
      <X aria-hidden="true" />
    </Button>
  );
}
