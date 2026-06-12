import Link from "next/link";
import { format } from "date-fns";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { listJobs } from "@/lib/api";

export default async function JobsPage() {
  const jobs = await listJobs().catch(() => []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Jobs</h1>
        <p className="mt-2 text-sm text-muted-foreground">Uploaded lead files and validation counts.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Import history</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-3 pr-4">File</th>
                  <th className="py-3 pr-4">Status</th>
                  <th className="py-3 pr-4">Rows</th>
                  <th className="py-3 pr-4">Accepted</th>
                  <th className="py-3 pr-4">Rejected</th>
                  <th className="py-3 pr-4">Created</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b last:border-0">
                    <td className="py-3 pr-4 font-medium">
                      <Link className="hover:underline" href={`/jobs/${job.id}`}>
                        {job.source_filename}
                      </Link>
                    </td>
                    <td className="py-3 pr-4">{job.status}</td>
                    <td className="py-3 pr-4">{job.total_rows}</td>
                    <td className="py-3 pr-4">{job.valid_rows}</td>
                    <td className="py-3 pr-4">{job.invalid_rows}</td>
                    <td className="py-3 pr-4">{format(new Date(job.created_at), "yyyy-MM-dd HH:mm")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {jobs.length === 0 ? <p className="py-6 text-sm text-muted-foreground">No jobs have been uploaded yet.</p> : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

