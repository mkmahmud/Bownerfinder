import Link from "next/link";
import { BarChart3, BriefcaseBusiness, Settings, Table, Upload } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/results", label: "Results", icon: Table },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppNav() {
  return (
    <aside className="flex w-full shrink-0 border-b bg-white md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex w-full flex-col">
        <div className="border-b px-5 py-4">
          <Link href="/dashboard" className="text-base font-semibold tracking-normal">
            Bownerfinder
          </Link>
          <p className="mt-1 text-xs text-muted-foreground">Local lead enrichment</p>
        </div>
        <nav className="flex gap-1 overflow-x-auto p-3 md:flex-col">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="inline-flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <link.icon className="h-4 w-4" aria-hidden="true" />
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}

