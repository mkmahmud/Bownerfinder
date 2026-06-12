"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { AlertCircle, CheckCircle2, FileSpreadsheet, Loader2, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { type UploadResponse, uploadLeads } from "@/lib/api";

const MAX_BYTES = 25 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = [".csv", ".xlsx"];

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [response, setResponse] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileError = useMemo(() => validateFile(file), [file]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setResponse(null);
    setError(null);
    if (!file || fileError) {
      setError(fileError ?? "Choose a CSV or XLSX file before uploading.");
      return;
    }

    setIsUploading(true);
    try {
      setResponse(await uploadLeads(file));
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Upload leads</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Import CSV or XLSX files with a required business_name column and optional website, phone, email, linkedin,
          facebook, and instagram columns.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lead file</CardTitle>
          <CardDescription>Files stay on this machine and are stored with the created job.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/40 p-6 text-center hover:bg-muted">
              <UploadCloud className="h-9 w-9 text-muted-foreground" aria-hidden="true" />
              <span className="mt-3 text-sm font-medium">{file ? file.name : "Choose a CSV or XLSX file"}</span>
              <span className="mt-1 text-xs text-muted-foreground">Maximum size: 25 MB</span>
              <Input
                className="sr-only"
                type="file"
                accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
            </label>

            {fileError ? (
              <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" aria-hidden="true" />
                {fileError}
              </div>
            ) : null}

            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" disabled={isUploading || Boolean(fileError)}>
                {isUploading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />}
                Upload file
              </Button>
              {file ? <span className="text-sm text-muted-foreground">{formatBytes(file.size)}</span> : null}
            </div>
          </form>
        </CardContent>
      </Card>

      {error ? (
        <Card className="border-destructive/40">
          <CardContent className="flex items-start gap-3 pt-6 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </CardContent>
        </Card>
      ) : null}

      {response ? (
        <Card className="border-primary/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-primary" aria-hidden="true" />
              Job created
            </CardTitle>
            <CardDescription>{response.job.source_filename}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Total rows" value={response.job.total_rows} />
              <Metric label="Accepted" value={response.job.valid_rows} />
              <Metric label="Rejected" value={response.job.invalid_rows} />
            </div>
            {response.errors.length > 0 ? (
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-sm font-medium">Rows needing correction</p>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {response.errors.slice(0, 6).map((rowError) => (
                    <li key={`${rowError.row_number}-${rowError.message}`}>
                      Row {rowError.row_number}: {rowError.message}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <div>
              <Button asChild variant="outline">
                <Link href={`/jobs/${response.job.id}`}>View job</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-normal">{value}</div>
    </div>
  );
}

function validateFile(file: File | null): string | null {
  if (!file) {
    return null;
  }
  const lowerName = file.name.toLowerCase();
  if (!ACCEPTED_EXTENSIONS.some((extension) => lowerName.endsWith(extension))) {
    return "Only CSV and XLSX files are supported.";
  }
  if (file.size > MAX_BYTES) {
    return "File exceeds the 25 MB limit.";
  }
  return null;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

