"use client";

interface ConversationStartersProps {
  starters: string[];
  onSelect: (text: string) => void;
}

export function ConversationStarters({ starters, onSelect }: ConversationStartersProps) {
  const items = starters.length > 0 ? starters.slice(0, 4) : ["Ask me anything"];

  return (
    <div className="flex flex-wrap justify-center gap-2 px-4 py-3">
      {items.map((text) => (
        <button
          key={text}
          onClick={() => onSelect(text)}
          className="rounded-full border border-border bg-card px-4 py-2 text-sm transition-colors hover:border-primary/30 hover:bg-accent/50"
        >
          {text}
        </button>
      ))}
    </div>
  );
}
