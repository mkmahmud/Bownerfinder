import Link from "next/link";

import { ResultsBrowser } from "@/components/results-browser";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getJobStats, listJobs, listResults } from "@/lib/api";

type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ResultsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const query = typeof params.q === "string" ? params.q : undefined;
  const jobId = typeof params.job_id === "string" ? params.job_id : undefined;
  const status = typeof params.status === "string" ? params.status : undefined;
  const sort = typeof params.sort === "string" ? params.sort : undefined;

  const [jobs, stats, rows] = await Promise.all([
    listJobs().catch(() => []),
    getJobStats().catch(() => null),
    listResults({ query, jobId, status, sort }).catch(() => []),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Results</h1>
          <p className="mt-2 text-sm text-muted-foreground">Search and export the enriched local result set.</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/jobs">View jobs</Link>
        </Button>
      </div>

      {stats ? (
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <Metric title="Jobs" value={stats.total_jobs} />
          <Metric title="Running" value={stats.running_jobs} />
          <Metric title="Completed" value={stats.completed_jobs} />
          <Metric title="Failed" value={stats.failed_jobs} />
          <Metric title="Companies" value={stats.companies_total} />
          <Metric title="Enriched" value={stats.companies_enriched} />
        </div>
      ) : null}

      <ResultsBrowser rows={rows} jobId={jobId} query={query} sort={sort} status={status} />

      <Card>
        <CardHeader>
          <CardTitle>Jobs with results</CardTitle>
          <CardDescription>Open the originating import job for a full per-file view.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {jobs.map((job) => (
              <Card key={job.id}>
                <CardHeader>
                  <CardTitle className="text-base">{job.source_filename}</CardTitle>
                  <CardDescription>
                    {job.status} · {job.valid_rows} valid rows
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button asChild variant="outline">
                    <Link href={`/jobs/${job.id}`}>Open job</Link>
                  </Button>
                </CardContent>
              </Card>
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
        <div className="text-2xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}

