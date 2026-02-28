"use client";

import type { ConversationScope } from "@/lib/chat-types";

interface ScopedChatHeaderProps {
  scope: ConversationScope;
  onNewChat: () => void;
}

export function ScopedChatHeader({ scope, onNewChat }: ScopedChatHeaderProps) {
  return (
    <div className="flex items-center gap-3 border-b border-border bg-background px-4 py-2.5">
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-[10px] font-bold text-white"
        style={{ backgroundColor: scope.displayColor }}
      >
        {scope.displayAvatar}
      </div>
      <span className="text-sm font-semibold">{scope.displayTitle}</span>
      <span className="rounded-full border border-border px-2 py-0.5 text-[10px] text-muted-foreground">
        {scope.type}
      </span>
      <div className="flex-1" />
      <button
        onClick={onNewChat}
        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
        </svg>
        New chat
      </button>
    </div>
  );
}
