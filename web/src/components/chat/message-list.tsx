"use client";

import { useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/chat-types";
import { MessageBubble } from "./message-bubble";
import { ThinkingIndicator } from "./thinking-indicator";

interface MessageListProps {
  messages: ChatMessage[];
  isThinking: boolean;
}

export function MessageList({ messages, isThinking }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  if (messages.length === 0 && !isThinking) {
    return null;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto max-w-2xl space-y-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isThinking && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
