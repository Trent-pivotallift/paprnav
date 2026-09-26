import { createElement } from "react";

export interface PilotOcrSummary {
  recordedRunsOnly: boolean;
  paidAttemptCoverageComplete: boolean;
  recordedRunCount: number;
  lifecycleCounts: Record<string, number>;
  pricingCounts: Record<string, number>;
  attributionCounts: Record<string, number>;
  billingCounts: Record<string, number>;
  reconciliationRequiredRunCount: number;
  unknownAmountRunCount: number;
  knownPartialEstimateUsd: number | null;
  completedPricedEstimateUsd: number | null;
}

const CATEGORY_GROUPS = [
  {
    title: "Lifecycle",
    counts: "lifecycleCounts",
    categories: [
      ["completed", "Completed"],
      ["failed", "Failed"],
      ["pending", "Pending"],
    ],
  },
  {
    title: "Pricing",
    counts: "pricingCounts",
    categories: [
      ["priced", "Priced"],
      ["unpriced", "Unpriced"],
    ],
  },
  {
    title: "Recorded attribution",
    counts: "attributionCounts",
    categories: [
      ["attributed", "Attributed"],
      ["unattributed", "Unattributed"],
    ],
  },
  {
    title: "Billing",
    counts: "billingCounts",
    categories: [
      ["chargeable", "Chargeable"],
      ["not_billable", "Not billable"],
      ["credited", "Credited"],
      ["disputed", "Disputed"],
      ["other", "Other"],
    ],
  },
] as const;

function formatUsd(value: number | null): string {
  return value === null ? "Unknown" : `$${value.toFixed(4)}`;
}

export function PilotOcrSummaryDetails({ ocr }: { ocr: PilotOcrSummary }) {
  return createElement(
    "div",
    { className: "space-y-3 text-sm", "data-testid": "pilot-ocr-details" },
    createElement(
      "p",
      { className: "text-2xl font-semibold", "data-testid": "partial-recorded-estimate" },
      `Partial recorded-run estimate: ${formatUsd(ocr.knownPartialEstimateUsd)}`,
    ),
    createElement(
      "p",
      { "data-testid": "completed-priced-estimate" },
      `Completed priced estimate: ${formatUsd(ocr.completedPricedEstimateUsd)}`,
    ),
    createElement("p", null, `${ocr.recordedRunCount} recorded runs`),
    createElement(
      "div",
      { className: "grid gap-3 sm:grid-cols-2" },
      ...CATEGORY_GROUPS.map((group) => {
        const counts = ocr[group.counts];
        return createElement(
          "div",
          { className: "rounded border p-2", key: group.title },
          createElement("p", { className: "font-medium" }, group.title),
          createElement(
            "ul",
            { className: "mt-1 space-y-1 text-xs" },
            ...group.categories.map(([key, label]) =>
              createElement("li", { key }, `${label}: ${counts[key] ?? 0}`),
            ),
          ),
        );
      }),
    ),
    createElement(
      "p",
      null,
      `${ocr.unknownAmountRunCount} unknown amounts · ${ocr.reconciliationRequiredRunCount} require reconciliation`,
    ),
    createElement(
      "p",
      { className: "text-xs text-muted-foreground" },
      "Recorded runs only; the combined known amount is a partial recorded-run estimate and paid-attempt coverage is incomplete.",
    ),
  );
}
