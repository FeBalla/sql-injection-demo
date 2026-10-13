import type { Metadata } from "next";

import { SqlInjectionLab } from "@/features/sql-injection/components/sql-injection-lab";

export const metadata: Metadata = {
  title: "SQL injection",
};

export default function SqlInjectionPage() {
  return <SqlInjectionLab />;
}
