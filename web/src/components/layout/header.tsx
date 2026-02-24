"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Header() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const crumbs = [{ label: "Dashboard", href: "/" }];

  if (segments[0] === "skills") {
    crumbs.push({ label: "Skills", href: "/skills" });
    if (segments[1]) {
      crumbs.push({ label: segments[1], href: `/skills` });
      if (segments[2]) {
        crumbs.push({
          label: segments[2],
          href: `/skills/${segments[1]}/${segments[2]}`,
        });
      }
    }
  }

  return (
    <header className="flex h-12 items-center border-b border-border/50 px-6">
      <nav className="flex items-center gap-1.5 text-sm">
        {crumbs.map((crumb, i) => (
          <span key={crumb.href} className="flex items-center gap-1.5">
            {i > 0 && (
              <span className="text-muted-foreground/50">/</span>
            )}
            {i === crumbs.length - 1 ? (
              <span className="font-medium text-foreground">{crumb.label}</span>
            ) : (
              <Link
                href={crumb.href}
                className="text-muted-foreground transition-colors hover:text-foreground"
              >
                {crumb.label}
              </Link>
            )}
          </span>
        ))}
      </nav>
    </header>
  );
}
