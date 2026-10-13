import type { SVGProps } from "react";

/** Apostrophe glyph from the design (lucide has no equivalent). */
export function ApostropheIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <path d="M7 7h4v4H7z" />
      <path d="M11 7c0 5-2 8-4 10" />
    </svg>
  );
}
