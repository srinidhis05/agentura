"use client";

interface SkillNode {
  name: string;
  role: string;
  model?: string;
}

interface TopologyEdge {
  from_skill: string;
  to_skill: string;
  route_condition?: string;
}

interface SkillDAGProps {
  skills: SkillNode[];
  topology?: TopologyEdge[];
  domain: string;
}

const roleColors: Record<string, string> = {
  manager: "border-blue-500/30 bg-blue-500/10 text-blue-400",
  specialist: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400",
  field: "border-amber-500/30 bg-amber-500/10 text-amber-400",
};

export function SkillDAG({ skills, topology, domain }: SkillDAGProps) {
  if (!skills || skills.length === 0) return null;

  const managers = skills.filter((s) => s.role === "manager");
  const specialists = skills.filter((s) => s.role === "specialist");
  const fieldAgents = skills.filter((s) => s.role === "field");

  return (
    <div className="space-y-4">
      <h3 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Skill Topology
      </h3>
      <div className="flex flex-col items-center gap-3">
        {managers.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2">
            {managers.map((s) => (
              <SkillBox key={s.name} skill={s} domain={domain} />
            ))}
          </div>
        )}
        {(managers.length > 0 && (specialists.length > 0 || fieldAgents.length > 0)) && (
          <svg className="h-4 w-4 text-muted-foreground/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        )}
        {specialists.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2">
            {specialists.map((s) => (
              <SkillBox key={s.name} skill={s} domain={domain} />
            ))}
          </div>
        )}
        {(specialists.length > 0 && fieldAgents.length > 0) && (
          <svg className="h-4 w-4 text-muted-foreground/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        )}
        {fieldAgents.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2">
            {fieldAgents.map((s) => (
              <SkillBox key={s.name} skill={s} domain={domain} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SkillBox({ skill, domain }: { skill: SkillNode; domain: string }) {
  const color = roleColors[skill.role] ?? "border-gray-500/30 bg-gray-500/10 text-gray-400";
  return (
    <a href={`/dashboard/skills/${domain}/${skill.name}`}>
      <div className={`rounded-lg border px-3 py-2 text-center transition-all hover:opacity-80 ${color}`}>
        <p className="text-xs font-medium">{skill.name}</p>
        <p className="text-[9px] text-muted-foreground">{skill.role}</p>
      </div>
    </a>
  );
}
