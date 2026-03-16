/** Centralized dual-mode color maps for the dashboard. */

export const domainColors: Record<string, { bg: string; border: string; text: string }> = {
  ecm: {
    bg: "bg-amber-50 dark:bg-amber-500/10",
    border: "border-amber-300 dark:border-amber-500/30",
    text: "text-amber-700 dark:text-amber-400",
  },
  incubator: {
    bg: "bg-violet-50 dark:bg-violet-500/10",
    border: "border-violet-300 dark:border-violet-500/30",
    text: "text-violet-700 dark:text-violet-400",
  },
  ge: {
    bg: "bg-emerald-50 dark:bg-emerald-500/10",
    border: "border-emerald-300 dark:border-emerald-500/30",
    text: "text-emerald-700 dark:text-emerald-400",
  },
  growth: {
    bg: "bg-teal-50 dark:bg-teal-500/10",
    border: "border-teal-300 dark:border-teal-500/30",
    text: "text-teal-700 dark:text-teal-400",
  },
  pm: {
    bg: "bg-blue-50 dark:bg-blue-500/10",
    border: "border-blue-300 dark:border-blue-500/30",
    text: "text-blue-700 dark:text-blue-400",
  },
  dev: {
    bg: "bg-rose-50 dark:bg-rose-500/10",
    border: "border-rose-300 dark:border-rose-500/30",
    text: "text-rose-700 dark:text-rose-400",
  },
};

export const domainFallback = {
  bg: "bg-gray-50 dark:bg-gray-500/10",
  border: "border-gray-300 dark:border-gray-500/30",
  text: "text-gray-600 dark:text-gray-400",
};

export const domainLabels: Record<string, string> = {
  ecm: "ECM",
  incubator: "Incubator",
  ge: "Global Equities",
  growth: "Growth Analytics",
  pm: "Product Management",
  dev: "Engineering",
};

export const domainLabelsLong: Record<string, string> = {
  ecm: "ECM (Remittance Ops)",
  incubator: "Incubator (Build Pipeline)",
  ge: "Global Equities",
  growth: "Growth Analytics (Sentinel)",
  pm: "Product Management",
  dev: "Engineering",
};

/** Agent card gradient backgrounds (used in agents list - light gets white card + left border) */
export const domainCardAccent: Record<string, string> = {
  ecm: "border-l-amber-400",
  incubator: "border-l-violet-400",
  ge: "border-l-emerald-400",
  growth: "border-l-teal-400",
  pm: "border-l-blue-400",
  dev: "border-l-rose-400",
};

export const roleColors: Record<string, string> = {
  manager: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-400 dark:border-blue-500/30",
  specialist: "bg-purple-100 text-purple-700 border-purple-200 dark:bg-purple-500/20 dark:text-purple-400 dark:border-purple-500/30",
  field: "bg-green-100 text-green-700 border-green-200 dark:bg-green-500/20 dark:text-green-400 dark:border-green-500/30",
  agent: "bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-500/20 dark:text-gray-400 dark:border-gray-500/30",
};

export const roleIcons: Record<string, string> = {
  manager: "M",
  specialist: "S",
  field: "F",
  agent: "A",
};

export const statusDot: Record<string, string> = {
  idle: "bg-gray-400",
  working: "bg-amber-400 animate-pulse",
  paused: "bg-yellow-400",
  terminated: "bg-red-400",
};

export const statusColors: Record<string, string> = {
  idle: "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
  working: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
  paused: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400",
  terminated: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
};

export const executorBadge: Record<string, string> = {
  "claude-code": "bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-400",
  ptc: "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/20 dark:text-cyan-400",
};

export const outcomeStyles: Record<string, string> = {
  accepted: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20",
  corrected: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:border-amber-500/20",
  pending_review: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/10 dark:text-blue-400 dark:border-blue-500/20",
  pending_approval: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:border-orange-500/20",
  approved: "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-500/10 dark:text-teal-400 dark:border-teal-500/20",
  executed: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20",
  approved_failed: "bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20",
  rejected: "bg-red-100 text-red-700 border-red-200 dark:bg-red-500/10 dark:text-red-400 dark:border-red-500/20",
};

export const heartbeatStatusColors: Record<string, string> = {
  running: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
  completed: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400",
  failed: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
  skipped: "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
};

export const ticketStatusColors: Record<string, string> = {
  open: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-400 dark:border-blue-500/30",
  in_progress: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-500/20 dark:text-amber-400 dark:border-amber-500/30",
  resolved: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30",
  escalated: "bg-red-100 text-red-700 border-red-200 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30",
  cancelled: "bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-500/20 dark:text-gray-400 dark:border-gray-500/30",
};

export const ticketColumnColors: Record<string, string> = {
  open: "border-blue-400 dark:border-blue-500/40",
  in_progress: "border-amber-400 dark:border-amber-500/40",
  resolved: "border-emerald-400 dark:border-emerald-500/40",
  escalated: "border-red-400 dark:border-red-500/40",
};

export const priorityColors: Record<number, string> = {
  1: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
  2: "bg-orange-100 text-orange-700 dark:bg-orange-500/20 dark:text-orange-400",
  3: "bg-yellow-100 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-400",
  4: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
  5: "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
};

export const priorityConfig: Record<number, { label: string; color: string }> = {
  1: { label: "Critical", color: "bg-red-100 text-red-700 border-red-200 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30" },
  2: { label: "High", color: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-500/20 dark:text-orange-400 dark:border-orange-500/30" },
  3: { label: "Medium", color: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-500/20 dark:text-yellow-400 dark:border-yellow-500/30" },
  4: { label: "Low", color: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-500/20 dark:text-blue-400 dark:border-blue-500/30" },
  5: { label: "Minimal", color: "bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-500/20 dark:text-gray-400 dark:border-gray-500/30" },
};

export const fleetStatusColors: Record<string, { bg: string; text: string }> = {
  pending: { bg: "bg-gray-100 dark:bg-gray-500/15", text: "text-gray-600 dark:text-gray-400" },
  running: { bg: "bg-blue-100 dark:bg-blue-500/15", text: "text-blue-700 dark:text-blue-400" },
  completed: { bg: "bg-emerald-100 dark:bg-emerald-500/15", text: "text-emerald-700 dark:text-emerald-400" },
  failed: { bg: "bg-red-100 dark:bg-red-500/15", text: "text-red-700 dark:text-red-400" },
  cancelled: { bg: "bg-amber-100 dark:bg-amber-500/15", text: "text-amber-700 dark:text-amber-400" },
};

export const fleetStatusDot: Record<string, string> = {
  pending: "bg-gray-500",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-emerald-500",
  failed: "bg-red-500",
  cancelled: "bg-amber-500",
};

export const miniStatColors: Record<string, string> = {
  "text-blue-400": "text-blue-600 dark:text-blue-400",
  "text-amber-400": "text-amber-600 dark:text-amber-400",
  "text-emerald-400": "text-emerald-600 dark:text-emerald-400",
  "text-red-400": "text-red-600 dark:text-red-400",
};

export const orgChartDomainColors: Record<string, string> = {
  ecm: "border-amber-300 bg-amber-50 dark:border-amber-500/40 dark:bg-amber-500/10",
  incubator: "border-violet-300 bg-violet-50 dark:border-violet-500/40 dark:bg-violet-500/10",
  ge: "border-emerald-300 bg-emerald-50 dark:border-emerald-500/40 dark:bg-emerald-500/10",
  growth: "border-teal-300 bg-teal-50 dark:border-teal-500/40 dark:bg-teal-500/10",
  pm: "border-blue-300 bg-blue-50 dark:border-blue-500/40 dark:bg-blue-500/10",
  dev: "border-rose-300 bg-rose-50 dark:border-rose-500/40 dark:bg-rose-500/10",
};

export const traceBorderColors: Record<string, string> = {
  tool_call: "border-l-blue-400 dark:border-l-blue-500/60",
  status_change: "border-l-amber-400 dark:border-l-amber-500/60",
  delegation: "border-l-purple-400 dark:border-l-purple-500/60",
  escalation: "border-l-red-400 dark:border-l-red-500/60",
  note: "border-l-gray-400 dark:border-l-gray-500/60",
};

/** Transcript entry type badges (Paperclip-style) */
export const transcriptTypeBadge: Record<string, string> = {
  stderr: "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400",
  init: "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
  assistant: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
  tool_call: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
  tool_result: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400",
  user: "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400",
  system: "bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400",
};

export const transcriptTypeBorder: Record<string, string> = {
  stderr: "border-l-red-400 dark:border-l-red-500/60",
  init: "border-l-gray-300 dark:border-l-gray-500/40",
  assistant: "border-l-blue-400 dark:border-l-blue-500/60",
  tool_call: "border-l-amber-400 dark:border-l-amber-500/60",
  tool_result: "border-l-emerald-400 dark:border-l-emerald-500/60",
  user: "border-l-purple-400 dark:border-l-purple-500/60",
  system: "border-l-gray-300 dark:border-l-gray-500/40",
};

export const triggerBadgeColors: Record<string, string> = {
  schedule: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400",
  manual: "bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400",
  webhook: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
  ticket: "bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400",
};
