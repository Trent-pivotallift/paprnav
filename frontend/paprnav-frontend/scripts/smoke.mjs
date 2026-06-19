const baseUrl = process.env.PAPRNAV_FRONTEND_URL ?? "http://localhost:3000";
const email = process.env.PAPRNAV_SMOKE_EMAIL ?? "owner.demo@paprnav.local";
const password = process.env.PAPRNAV_SMOKE_PASSWORD ?? "demo-password";

const requiredRoutes = [
  "/",
  "/register",
  "/logbook",
  "/profile",
  "/logbook/N123AB?logbook=airframe",
  "/logbook/N123AB/new?logbook=airframe",
  "/logbook/N123AB/upload?logbook=airframe",
];

let cookie = "";

function url(path) {
  return new URL(path, baseUrl).toString();
}

function updateCookie(response) {
  const setCookie = response.headers.get("set-cookie");
  if (!setCookie) {
    return;
  }

  cookie = setCookie
    .split(",")
    .map((part) => part.split(";")[0])
    .filter((part) => part.includes("="))
    .join("; ");
}

async function request(path, init = {}) {
  const headers = new Headers(init.headers);
  const isFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (cookie) {
    headers.set("cookie", cookie);
  }
  if (init.body && !headers.has("content-type") && !isFormData) {
    headers.set("content-type", "application/json");
  }

  const response = await fetch(url(path), { ...init, headers });
  updateCookie(response);
  return response;
}

async function expectOk(path, init = {}) {
  const response = await request(path, init);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${init.method ?? "GET"} ${path} returned ${response.status}: ${body.slice(0, 300)}`);
  }
  return response;
}

for (const route of requiredRoutes) {
  await expectOk(route);
  console.log(`ok route ${route}`);
}

await expectOk("/api/backend/api/v1/auth/login", {
  method: "POST",
  body: JSON.stringify({ email, password }),
});
console.log(`ok login ${email}`);

const aircraftResponse = await expectOk("/api/backend/api/v1/aircraft");
const aircraftPayload = await aircraftResponse.json();
const aircraft = aircraftPayload.aircraft.find((item) => item.nNumberNormalized === "N123AB");
if (!aircraft) {
  throw new Error("N123AB was not visible to the smoke-test user.");
}
console.log(`ok aircraft ${aircraft.id}`);

const entryResponse = await expectOk(`/api/backend/api/v1/aircraft/${aircraft.id}/logbook-entries`, {
  method: "POST",
  body: JSON.stringify({
    section: "airframe",
    entryDate: "2026-06-18",
    description: `Smoke test manual entry ${Date.now()}`,
    performerName: "Smoke Tester",
    performerCredential: "A&P",
    tachTime: 1,
  }),
});
const entry = await entryResponse.json();
if (!entry.id || entry.sourceType !== "manual") {
  throw new Error("Manual entry smoke workflow did not return a valid entry.");
}
console.log(`ok manual-entry ${entry.id}`);

const uploadFormData = new FormData();
uploadFormData.set("section", "airframe");
uploadFormData.set(
  "file",
  new File(["%PDF-1.4 paprnav smoke OCR fixture"], `smoke-ocr-${Date.now()}.pdf`, { type: "application/pdf" }),
);

const uploadResponse = await expectOk(`/api/backend/api/v1/aircraft/${aircraft.id}/uploads`, {
  method: "POST",
  body: uploadFormData,
});
const uploadPayload = await uploadResponse.json();
if (!uploadPayload.upload?.id || !uploadPayload.ingestionJob?.id) {
  throw new Error("OCR smoke upload did not return both upload and ingestion job IDs.");
}
console.log(`ok upload ${uploadPayload.upload.id}`);
console.log(`ok ingestion-job ${uploadPayload.ingestionJob.id}`);

await expectOk(`/logbook/N123AB/ingestion/${uploadPayload.ingestionJob.id}`);
console.log(`ok route /logbook/N123AB/ingestion/${uploadPayload.ingestionJob.id}`);
