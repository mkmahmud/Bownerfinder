import Link from "next/link";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getJobStats, listJobs } from "@/lib/api";

export default async function DashboardPage() {
  const [jobs, stats] = await Promise.all([listJobs().catch(() => []), getJobStats().catch(() => null)]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Dashboard</h1>
          <p className="mt-2 text-sm text-muted-foreground">Local enrichment activity across imports, results, and exports.</p>
        </div>
        <Button asChild>
          <Link href="/upload">
            <Upload className="h-4 w-4" aria-hidden="true" />
            Upload leads
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <Metric title="Jobs" value={stats?.total_jobs ?? jobs.length} />
        <Metric title="Running" value={stats?.running_jobs ?? 0} />
        <Metric title="Completed" value={stats?.completed_jobs ?? 0} />
        <Metric title="Failed" value={stats?.failed_jobs ?? 0} />
        <Metric title="Companies" value={stats?.companies_total ?? 0} />
        <Metric title="Enriched" value={stats?.companies_enriched ?? 0} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {jobs.slice(0, 6).map((job) => (
              <div key={job.id} className="rounded-md border p-4">
                <div className="font-medium">{job.source_filename}</div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {job.status} · {job.valid_rows} valid · {job.invalid_rows} rejected
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
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

