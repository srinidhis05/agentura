"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getOrgChart } from "@/lib/api";
import type { OrgChartNode } from "@/lib/types";
import {
  orgChartDomainColors,
  domainLabels,
  roleIcons,
  statusDot,
} from "@/lib/colors";

function buildTree(flatNodes: OrgChartNode[]): OrgChartNode[] {
  const nodeMap = new Map<string, OrgChartNode>();
  const roots: OrgChartNode[] = [];

  for (const node of flatNodes) {
    nodeMap.set(node.id, { ...node, children: [] });
  }

  for (const node of flatNodes) {
    const current = nodeMap.get(node.id)!;
    if (node.reports_to && nodeMap.has(node.reports_to)) {
      nodeMap.get(node.reports_to)!.children!.push(current);
    } else {
      roots.push(current);
    }
  }

  return roots;
}

function groupByDomain(roots: OrgChartNode[]): Record<string, OrgChartNode[]> {
  const groups: Record<string, OrgChartNode[]> = {};
  for (const root of roots) {
    const d = root.domain || "other";
    if (!groups[d]) groups[d] = [];
    groups[d].push(root);
  }
  return groups;
}

function TreeNode({ node }: { node: OrgChartNode }) {
  return (
    <div className="relative">
      <Link
        href={`/dashboard/agents/${node.id}`}
        className={`group flex items-center gap-3 rounded-lg border p-3 transition-all hover:shadow-md hover:scale-[1.02] ${
          orgChartDomainColors[node.domain] || "border-gray-300 bg-gray-50 dark:border-gray-500/40 dark:bg-gray-500/10"
        }`}
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-muted dark:bg-card/80 text-xs font-bold text-foreground">
          {roleIcons[node.role] || "A"}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground truncate">
              {node.display_name || node.name}
            </span>
            <div className={`h-2 w-2 rounded-full flex-shrink-0 ${statusDot[node.status] || statusDot.idle}`} />
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{node.role}</span>
            {node.executor && (
              <>
                <span className="text-border">|</span>
                <span>{node.executor}</span>
              </>
            )}
          </div>
        </div>
      </Link>

      {node.children && node.children.length > 0 && (
        <div className="ml-6 mt-2 space-y-2 border-l border-border pl-4">
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function OrgChartPage() {
  const { data: flatNodes = [], isLoading } = useQuery({
    queryKey: ["org-chart"],
    queryFn: getOrgChart,
    refetchInterval: 15000,
  });

  const tree = buildTree(flatNodes);
  const domainGroups = groupByDomain(tree);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Org Chart</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Agent hierarchy across {Object.keys(domainGroups).length} domains
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 rounded-xl bg-muted dark:bg-card/50 animate-pulse border border-border" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {Object.entries(domainGroups).map(([domain, roots]) => (
            <div key={domain} className="rounded-xl border border-border bg-card shadow-sm p-4">
              <h2 className="text-lg font-semibold text-foreground mb-4">
                {domainLabels[domain] || domain}
              </h2>
              <div className="space-y-2">
                {roots.map((root) => (
                  <TreeNode key={root.id} node={root} />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
