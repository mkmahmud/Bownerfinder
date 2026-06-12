import Link from "next/link";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listJobs } from "@/lib/api";

export default async function DashboardPage() {
  const jobs = await listJobs().catch(() => []);
  const totals = jobs.reduce(
    (accumulator, job) => ({
      rows: accumulator.rows + job.total_rows,
      valid: accumulator.valid + job.valid_rows,
      invalid: accumulator.invalid + job.invalid_rows,
    }),
    { rows: 0, valid: 0, invalid: 0 },
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Dashboard</h1>
          <p className="mt-2 text-sm text-muted-foreground">Phase 1 import activity from local jobs.</p>
        </div>
        <Button asChild>
          <Link href="/upload">
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload leads
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric title="Jobs" value={jobs.length} />
        <Metric title="Rows" value={totals.rows} />
        <Metric title="Accepted" value={totals.valid} />
        <Metric title="Rejected" value={totals.invalid} />
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}

