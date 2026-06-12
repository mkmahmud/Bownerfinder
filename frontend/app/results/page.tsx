import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listJobs } from "@/lib/api";

export default async function ResultsPage() {
  const jobs = await listJobs().catch(() => []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Results</h1>
        <p className="mt-2 text-sm text-muted-foreground">Phase 1 shows imported companies before enrichment begins.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job) => (
          <Card key={job.id}>
            <CardHeader>
              <CardTitle className="text-base">{job.source_filename}</CardTitle>
              <CardDescription>{job.valid_rows} companies imported</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline">
                <Link href={`/jobs/${job.id}`}>Open results</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
      {jobs.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Upload a lead file to create the first local result set.</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

