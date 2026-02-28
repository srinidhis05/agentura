import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage } from "@/lib/chat-types";
import { SkillResultCard } from "./skill-result-card";

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] rounded-2xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-full w-full">
        {/* Summary line above table */}
        {message.content && message.metadata?.tableData && (
          <p className="mb-2 text-sm text-muted-foreground">{message.content}</p>
        )}

        {/* Table data */}
        {message.metadata?.tableData && (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  {message.metadata.tableData.headers.map((h) => (
                    <th key={h} className="px-3 py-2 text-left font-semibold text-muted-foreground">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {message.metadata.tableData.rows.map((row, i) => (
                  <tr key={i} className="border-b border-border/50 last:border-0">
                    {row.map((cell, j) => (
                      <td key={j} className="px-3 py-2 font-mono">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Skill result card */}
        {message.metadata?.skillResult && (
          <SkillResultCard result={message.metadata.skillResult} />
        )}

        {/* Text content (only if no table) — rendered as markdown */}
        {message.content && !message.metadata?.tableData && (
          <article
            className={`prose prose-sm max-w-none prose-headings:text-foreground prose-p:text-foreground/80 prose-li:text-foreground/80 prose-strong:text-foreground prose-code:rounded prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:text-xs prose-code:text-foreground prose-code:before:content-none prose-code:after:content-none prose-pre:rounded-lg prose-pre:border prose-pre:border-border prose-pre:bg-muted prose-a:text-primary prose-hr:border-border ${message.metadata?.error ? "prose-p:text-red-600" : ""}`}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </article>
        )}
      </div>
    </div>
  );
}
