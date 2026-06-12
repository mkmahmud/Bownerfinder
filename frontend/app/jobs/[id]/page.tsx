import Link from "next/link";
import { notFound } from "next/navigation";

import { JobActions } from "@/components/job-actions";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type Company, type Job, listCompanies, request } from "@/lib/api";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function JobDetailPage({ params }: PageProps) {
  const { id } = await params;
  const job = await getJob(id);
  if (!job) {
    notFound();
  }
  const companies = await listCompanies(id).catch(() => []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">{job.source_filename}</h1>
          <p className="mt-2 text-sm text-muted-foreground">Job {job.id}</p>
        </div>
        <Button asChild variant="outline">
          <Link href="/jobs">Back to jobs</Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Metric title="Status" value={job.status} />
        <Metric title="Rows" value={job.total_rows.toString()} />
        <Metric title="Accepted" value={job.valid_rows.toString()} />
        <Metric title="Rejected" value={job.invalid_rows.toString()} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <JobActions jobId={job.id} status={job.status} />
        </CardContent>
      </Card>

      <CompanyTable companies={companies} />
    </div>
  );
}

async function getJob(id: string): Promise<Job | null> {
  try {
    return await request<Job>(`/jobs/${id}`);
  } catch (error) {
    if (error instanceof Error && error.message.toLowerCase().includes("not found")) {
      return null;
    }
    throw error;
  }
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-xl font-semibold tracking-normal">{value}</div>
      </CardContent>
    </Card>
  );
}

function CompanyTable({ companies }: { companies: Company[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Enriched companies</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1200px] text-left text-sm">
            <thead className="border-b text-xs uppercase text-muted-foreground">
              <tr>
                <th className="py-3 pr-4">Row</th>
                <th className="py-3 pr-4">Business</th>
                <th className="py-3 pr-4">Normalized</th>
                <th className="py-3 pr-4">Website</th>
                <th className="py-3 pr-4">Decision maker</th>
                <th className="py-3 pr-4">Title</th>
                <th className="py-3 pr-4">Email</th>
                <th className="py-3 pr-4">Phone</th>
                <th className="py-3 pr-4">Score</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((company) => (
                <tr key={company.id} className="border-b last:border-0">
                  <td className="py-3 pr-4">{company.row_number}</td>
                  <td className="py-3 pr-4 font-medium">{company.business_name}</td>
                  <td className="py-3 pr-4">{company.normalized_business_name}</td>
                  <td className="py-3 pr-4">{company.website ?? ""}</td>
                  <td className="py-3 pr-4">{company.decision_maker_name ?? ""}</td>
                  <td className="py-3 pr-4">{company.decision_maker_title ?? ""}</td>
                  <td className="py-3 pr-4">{company.email ?? ""}</td>
                  <td className="py-3 pr-4">{company.phone ?? ""}</td>
                  <td className="py-3 pr-4">{company.confidence_score ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {companies.length === 0 ? <p className="py-6 text-sm text-muted-foreground">No valid company rows were imported.</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}

