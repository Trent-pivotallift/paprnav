"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ClipboardCheck, FileSearch, Plane, Search, ShieldCheck } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  AirworthinessDirective,
  listAdExtractionReviews,
  listAirworthinessDirectives,
} from "@/lib/api";

export default function AirworthinessDirectivesPage() {
  const { user } = useAuth();
  const isAdmin = user?.memberships.some((membership) => membership.role === "platform_admin") ?? false;
  const [directives, setDirectives] = useState<AirworthinessDirective[]>([]);
  const [keyword, setKeyword] = useState("");
  const [adNumber, setAdNumber] = useState("");
  const [status, setStatus] = useState("");
  const [productType, setProductType] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [model, setModel] = useState("");
  const [query, setQuery] = useState({ keyword: "", adNumber: "", status: "", productType: "", manufacturer: "", model: "" });
  const [reviewCounts, setReviewCounts] = useState({ pending: 0, reviewed: 0, verified: 0, quarantined: 0, approvalReady: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const catalog = await listAirworthinessDirectives({
        q: query.keyword || undefined,
        adNumber: query.adNumber || undefined,
        status: query.status || undefined,
        productType: query.productType || undefined,
        manufacturer: query.manufacturer || undefined,
        model: query.model || undefined,
      });
      setDirectives(catalog);
      if (isAdmin) {
        const reviews = await listAdExtractionReviews(0, 1);
        setReviewCounts({ pending: reviews.pendingCount, reviewed: reviews.reviewedCount, verified: reviews.verifiedCount, quarantined: reviews.quarantinedCount, approvalReady: reviews.approvalReadyCount, total: reviews.totalCount });
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load the AD catalog.");
    } finally {
      setLoading(false);
    }
  }, [isAdmin, query]);

  useEffect(() => {
    void load();
  }, [load]);

  const currentCount = useMemo(() => directives.filter((directive) => directive.status === "current").length, [directives]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery({ keyword: keyword.trim(), adNumber: adNumber.trim(), status, productType, manufacturer: manufacturer.trim(), model: model.trim() });
  }

  function clear() {
    setKeyword("");
    setAdNumber("");
    setStatus("");
    setProductType("");
    setManufacturer("");
    setModel("");
    setQuery({ keyword: "", adNumber: "", status: "", productType: "", manufacturer: "", model: "" });
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <PageHeader
        title="AD currency & research"
        description="Search the released Airworthiness Directive catalog or start from an aircraft for an applicability-filtered view."
      />

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-3 py-5">
            <ShieldCheck className="h-8 w-8 text-primary" />
            <div><p className="text-2xl font-semibold">{directives.length}</p><p className="text-sm text-muted-foreground">Released results</p></div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-5">
            <FileSearch className="h-8 w-8 text-primary" />
            <div><p className="text-2xl font-semibold">{currentCount}</p><p className="text-sm text-muted-foreground">Current in these results</p></div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 py-5">
            <Plane className="h-8 w-8 text-primary" />
            <div><p className="font-medium">Need aircraft applicability?</p><Button asChild variant="link" className="h-auto p-0"><Link href="/logbook">Choose an aircraft</Link></Button></div>
          </CardContent>
        </Card>
      </div>

      {isAdmin ? (
        <Card className="mt-6 border-primary/30 bg-primary/5">
          <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex gap-3">
              <ClipboardCheck className="mt-0.5 h-6 w-6 text-primary" />
              <div>
                <p className="font-medium">Admin extraction review</p>
                <p className="text-sm text-muted-foreground">
                  {reviewCounts.verified} source-indexed out of {reviewCounts.total} · {reviewCounts.approvalReady} approval candidates · {reviewCounts.quarantined} source-quarantined · {reviewCounts.pending} decisions pending
                </p>
              </div>
            </div>
            <Button asChild><Link href="/logbook/ads/reviews">Open review queue</Link></Button>
          </CardContent>
        </Card>
      ) : null}

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Build an AD query</CardTitle>
          <p className="text-sm text-muted-foreground">
            This search is fleet-neutral. Only admin-reviewed directives are visible here; aircraft pages apply make, model, engine, propeller, and serial context automatically.
          </p>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1fr_1fr_11rem_1fr_1fr_11rem_auto] xl:items-end" onSubmit={submit}>
            <label className="space-y-2 text-sm font-medium">
              Keyword or title
              <Input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="e.g. seat rail inspection" />
            </label>
            <label className="space-y-2 text-sm font-medium">
              AD number
              <Input value={adNumber} onChange={(event) => setAdNumber(event.target.value)} placeholder="e.g. 95-21-15" />
            </label>
            <label className="space-y-2 text-sm font-medium">
              Product type
              <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={productType} onChange={(event) => setProductType(event.target.value)}>
                <option value="">All product types</option>
                <option value="aircraft">Aircraft</option>
                <option value="rotorcraft">Rotorcraft</option>
                <option value="engine">Engine</option>
                <option value="propeller">Propeller</option>
                <option value="appliance">Appliance</option>
                <option value="equipment">Equipment</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="space-y-2 text-sm font-medium">
              Manufacturer
              <Input value={manufacturer} onChange={(event) => setManufacturer(event.target.value)} placeholder="e.g. Textron Aviation" />
            </label>
            <label className="space-y-2 text-sm font-medium">
              Model
              <Input value={model} onChange={(event) => setModel(event.target.value)} placeholder="e.g. 172D" />
            </label>
            <label className="space-y-2 text-sm font-medium">
              Currency status
              <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">All statuses</option>
                <option value="current">Current</option>
                <option value="historical">Historical</option>
                <option value="superseded">Superseded</option>
              </select>
            </label>
            <div className="flex gap-2"><Button type="submit"><Search className="mr-2 h-4 w-4" />Search</Button><Button type="button" variant="outline" onClick={clear}>Clear</Button></div>
          </form>
        </CardContent>
      </Card>

      {error ? <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">{error}</p> : null}

      <section className="mt-8" aria-labelledby="catalog-results">
        <div className="flex items-end justify-between gap-4">
          <div><h2 id="catalog-results" className="text-xl font-semibold">Released directives</h2><p className="text-sm text-muted-foreground">{loading ? "Loading…" : `${directives.length} result${directives.length === 1 ? "" : "s"}`}</p></div>
        </div>
        <div className="mt-4 space-y-3">
          {!loading && directives.length === 0 ? <Card><CardContent className="py-10 text-center text-sm text-muted-foreground">No released ADs match this query.</CardContent></Card> : null}
          {directives.map((directive) => (
            <Card key={directive.id}>
              <CardContent className="flex flex-col gap-4 py-5 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">AD {directive.officialAdNumber ?? "Unnumbered"}</span>
                    <span className="rounded-full border px-2.5 py-1 text-xs capitalize">{directive.status}</span>
                  </div>
                  <h3 className="mt-2 font-semibold">{directive.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {directive.adNumber !== directive.officialAdNumber ? `Normalized ID ${directive.adNumber} · ` : ""}{directive.publicationDate ? `Published ${directive.publicationDate}` : "Publication date unavailable"}
                  </p>
                  {directive.applicabilityTargets.length ? <div className="mt-3 flex flex-wrap gap-2">{directive.applicabilityTargets.slice(0, 8).map((target, index) => <span key={`${target.groupKey ?? "target"}-${target.manufacturer ?? ""}-${target.model ?? ""}-${index}`} className="rounded-full border px-2 py-1 text-xs">{[target.productType, target.manufacturer, target.model].filter(Boolean).join(" · ")}</span>)}{directive.applicabilityTargets.length > 8 ? <span className="px-2 py-1 text-xs text-muted-foreground">+{directive.applicabilityTargets.length - 8} more</span> : null}</div> : null}
                </div>
                <div className="flex gap-2">
                  {directive.htmlUrl ? <Button asChild size="sm" variant="outline"><a href={directive.htmlUrl} target="_blank" rel="noreferrer">Source HTML</a></Button> : null}
                  {directive.pdfUrl ? <Button asChild size="sm" variant="outline"><a href={directive.pdfUrl} target="_blank" rel="noreferrer">Source PDF</a></Button> : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
