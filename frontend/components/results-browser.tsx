"use client";

import { useMemo, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { createExport, getExportDownloadUrl, type ResultRow } from "@/lib/api";

type Props = {
  rows: ResultRow[];
  jobId?: string;
  query?: string;
  sort?: string;
  status?: string;
};

export function ResultsBrowser({ rows, jobId, query, sort, status }: Props) {
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selectedIds = useMemo(() => Object.entries(selected).filter(([, value]) => value).map(([id]) => id), [selected]);

  async function exportRows(mode: "selected" | "all", format: "csv" | "xlsx") {
    setMessage(null);
    const payload = mode === "selected" && selectedIds.length > 0 ? { format, selected_company_ids: selectedIds, job_id: jobId } : { format, job_id: jobId };
    const exportRecord = await createExport(jobId ?? "", payload);
    setMessage(`Export ${exportRecord.status}: ${exportRecord.id}`);
    if (exportRecord.status === "completed") {
      window.location.href = getExportDownloadUrl(exportRecord.id);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="pt-6">
          <form className="grid gap-3 md:grid-cols-4" method="get">
            <input defaultValue={query ?? ""} name="q" placeholder="Search companies, names, email" className="h-10 rounded-md border bg-background px-3 text-sm" />
            <select defaultValue={status ?? ""} name="status" className="h-10 rounded-md border bg-background px-3 text-sm">
              <option value="">All statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
            <select defaultValue={sort ?? "confidence_score"} name="sort" className="h-10 rounded-md border bg-background px-3 text-sm">
              <option value="confidence_score">Confidence</option>
              <option value="business_name">Business name</option>
              <option value="decision_maker_name">Decision maker</option>
              <option value="updated_at">Updated</option>
            </select>
            <Button type="submit" variant="outline">Filter results</Button>
          </form>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <Button disabled={isPending} onClick={() => startTransition(() => exportRows("selected", "csv"))}>Export selected CSV</Button>
        <Button disabled={isPending} variant="outline" onClick={() => startTransition(() => exportRows("selected", "xlsx"))}>Export selected XLSX</Button>
        <Button disabled={isPending} variant="secondary" onClick={() => startTransition(() => exportRows("all", "csv"))}>Export all CSV</Button>
        <Button disabled={isPending} variant="outline" onClick={() => startTransition(() => exportRows("all", "xlsx"))}>Export all XLSX</Button>
        {message ? <span className="text-sm text-muted-foreground">{message}</span> : null}
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1100px] text-left text-sm">
              <thead className="border-b text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Select</th>
                  <th className="px-4 py-3">Company</th>
                  <th className="px-4 py-3">Decision maker</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Phone</th>
                  <th className="px-4 py-3">Website</th>
                  <th className="px-4 py-3">Score</th>
                  <th className="px-4 py-3">Evidence</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="border-b last:border-0">
                    <td className="px-4 py-3">
                      <Checkbox checked={selected[row.id] ?? false} onChange={(event) => setSelected((current) => ({ ...current, [row.id]: event.target.checked }))} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{row.business_name}</div>
                      <div className="text-xs text-muted-foreground">{row.normalized_business_name}</div>
                    </td>
                    <td className="px-4 py-3">{row.decision_maker_name ?? "Unassigned"}</td>
                    <td className="px-4 py-3">{row.decision_maker_title ?? "-"}</td>
                    <td className="px-4 py-3">{row.email ?? "-"}</td>
                    <td className="px-4 py-3">{row.phone ?? "-"}</td>
                    <td className="px-4 py-3">{row.website ?? "-"}</td>
                    <td className="px-4 py-3">{row.confidence_score ?? 0}</td>
                    <td className="px-4 py-3">{row.evidence_count} / {row.contact_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rows.length === 0 ? <p className="px-4 py-6 text-sm text-muted-foreground">No enrichment results match the current filters.</p> : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}