import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL } from "@/lib/api";

export default function SettingsPage() {
  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">Settings</h1>
        <p className="mt-2 text-sm text-muted-foreground">Local runtime configuration used by the frontend.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Backend API</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-3 text-sm">
            <div className="grid gap-1">
              <dt className="font-medium">API base URL</dt>
              <dd className="break-all text-muted-foreground">{API_BASE_URL}</dd>
            </div>
            <div className="grid gap-1">
              <dt className="font-medium">Accepted upload formats</dt>
              <dd className="text-muted-foreground">CSV, XLSX</dd>
            </div>
            <div className="grid gap-1">
              <dt className="font-medium">Pipeline mode</dt>
              <dd className="text-muted-foreground">Inline local execution with Redis/RQ fallback</dd>
            </div>
            <div className="grid gap-1">
              <dt className="font-medium">Maximum upload size</dt>
              <dd className="text-muted-foreground">25 MB</dd>
            </div>
            <div className="grid gap-1">
              <dt className="font-medium">AI model</dt>
              <dd className="text-muted-foreground">Ollama qwen3 or llama3</dd>
            </div>
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}

