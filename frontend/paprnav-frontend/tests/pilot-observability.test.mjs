import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { getPilotSummary, listVisibleObservability } from "../src/lib/api.ts";
import { PilotOcrSummaryDetails } from "../src/lib/pilot-ocr-summary.ts";

const EMPTY_OBSERVABILITY = {
  events: [],
  workflowEvents: [],
  feedback: [],
};

test("ordinary and platform-admin observability readers use distinct scopes", async () => {
  const requestedPaths = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    requestedPaths.push(String(input));
    return new Response(JSON.stringify(EMPTY_OBSERVABILITY), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  try {
    await listVisibleObservability(false, { status: "open" });
    await listVisibleObservability(true, { status: "open" });
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.deepEqual(requestedPaths, [
    "/api/v1/observability?status=open",
    "/api/v1/observability/admin?status=open",
  ]);
});

test("pilot summary client uses only the platform-admin endpoint", async () => {
  const requestedPaths = [];
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input) => {
    requestedPaths.push(String(input));
    return new Response(JSON.stringify({}), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  try {
    await getPilotSummary({ recentLimit: "10" });
  } finally {
    globalThis.fetch = originalFetch;
  }

  assert.deepEqual(requestedPaths, ["/api/v1/admin/pilot-summary?recentLimit=10"]);
});

test("pilot OCR summary renders every independent recorded-run category", () => {
  const markup = renderToStaticMarkup(PilotOcrSummaryDetails({
    ocr: {
      recordedRunsOnly: true,
      paidAttemptCoverageComplete: false,
      recordedRunCount: 3,
      lifecycleCounts: { completed: 1, failed: 1, pending: 1 },
      pricingCounts: { priced: 2, unpriced: 1 },
      attributionCounts: { attributed: 2, unattributed: 1 },
      billingCounts: {
        chargeable: 1,
        not_billable: 1,
        credited: 0,
        disputed: 1,
        other: 0,
      },
      reconciliationRequiredRunCount: 2,
      unknownAmountRunCount: 1,
      knownPartialEstimateUsd: 0.05,
      completedPricedEstimateUsd: 0.04,
    },
  }));

  for (const expected of [
    "Partial recorded-run estimate: $0.0500",
    "Completed priced estimate: $0.0400",
    "Lifecycle",
    "Completed: 1",
    "Failed: 1",
    "Pending: 1",
    "Pricing",
    "Priced: 2",
    "Unpriced: 1",
    "Recorded attribution",
    "Attributed: 2",
    "Unattributed: 1",
    "Billing",
    "Chargeable: 1",
    "Not billable: 1",
    "Credited: 0",
    "Disputed: 1",
    "Other: 0",
    "1 unknown amounts · 2 require reconciliation",
    "combined known amount is a partial recorded-run estimate",
    "paid-attempt coverage is incomplete",
  ]) {
    assert.match(markup, new RegExp(expected.replaceAll("$", "\\$&")));
  }
});
