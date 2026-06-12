"use client";

import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { createExport, getExportDownloadUrl, triggerEnrichment } from "@/lib/api";

type Props = {
  jobId: string;
  status: string;
};

export function JobActions({ jobId, status }: Props) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button
        disabled={isPending || status === "running"}
        onClick={() =>
          startTransition(async () => {
            try {
              setMessage(null);
              const updated = await triggerEnrichment(jobId, { mode: "rerun" });
              setMessage(`Job ${updated.status}`);
            } catch (error) {
              setMessage(error instanceof Error ? error.message : "Unable to re-run enrichment.");
            }
          })
        }
      >
        Re-run enrichment
      </Button>
      <Button
        variant="outline"
        disabled={isPending}
        onClick={() =>
          startTransition(async () => {
            try {
              setMessage(null);
              const exportRecord = await createExport(jobId, { format: "csv", job_id: jobId });
              setMessage(`Export ${exportRecord.status}`);
              if (exportRecord.status === "completed") {
                window.location.href = getExportDownloadUrl(exportRecord.id);
              }
            } catch (error) {
              setMessage(error instanceof Error ? error.message : "Unable to export CSV.");
            }
          })
        }
      >
        Export CSV
      </Button>
      <Button
        variant="outline"
        disabled={isPending}
        onClick={() =>
          startTransition(async () => {
            try {
              setMessage(null);
              const exportRecord = await createExport(jobId, { format: "xlsx", job_id: jobId });
              setMessage(`Export ${exportRecord.status}`);
              if (exportRecord.status === "completed") {
                window.location.href = getExportDownloadUrl(exportRecord.id);
              }
            } catch (error) {
              setMessage(error instanceof Error ? error.message : "Unable to export XLSX.");
            }
          })
        }
      >
        Export XLSX
      </Button>
      {message ? <span className="text-sm text-muted-foreground">{message}</span> : null}
    </div>
  );
}