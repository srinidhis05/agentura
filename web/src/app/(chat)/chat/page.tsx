"use client";

import { useReducer, useEffect, useState, useCallback } from "react";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { MessageList } from "@/components/chat/message-list";
import { MessageInput } from "@/components/chat/message-input";
import { chatReducer, initialState, saveState, loadState } from "@/lib/chat-reducer";
import { routeCommand } from "@/lib/chat-router";
import type { ChatMessage } from "@/lib/chat-types";

const SUGGESTED_ACTIONS = [
  { label: "List agents", command: "get skills" },
  { label: "Platform status", command: "status" },
  { label: "Recent executions", command: "get executions" },
  { label: "Show domains", command: "get domains" },
  { label: "Memory status", command: "memory status" },
  { label: "Help", command: "help" },
];

export default function ChatPage() {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from localStorage
  useEffect(() => {
    const saved = loadState();
    if (saved && saved.conversations.length > 0) {
      dispatch({ type: "LOAD_STATE", state: saved });
    } else {
      dispatch({ type: "NEW_CONVERSATION" });
    }
    setHydrated(true);
  }, []);

  // Persist on state changes
  useEffect(() => {
    if (hydrated) saveState(state);
  }, [state, hydrated]);

  const activeConversation = state.conversations.find(
    (c) => c.id === state.activeConversationId,
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !state.activeConversationId) return;

      const userMsg: ChatMessage = {
        id: `${Date.now()}-user`,
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };

      dispatch({
        type: "ADD_MESSAGE",
        conversationId: state.activeConversationId,
        message: userMsg,
      });
      setInput("");
      setIsThinking(true);

      try {
        const response = await routeCommand(trimmed);
        dispatch({
          type: "ADD_MESSAGE",
          conversationId: state.activeConversationId,
          message: response,
        });
      } finally {
        setIsThinking(false);
      }
    },
    [state.activeConversationId],
  );

  const handleSuggestedAction = useCallback(
    (command: string) => {
      if (!state.activeConversationId) {
        dispatch({ type: "NEW_CONVERSATION" });
      }
      // Small delay to let new conversation be created
      setTimeout(() => sendMessage(command), 0);
    },
    [state.activeConversationId, sendMessage],
  );

  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const showWelcome = !activeConversation || activeConversation.messages.length === 0;

  return (
    <div className="flex h-screen">
      <ChatSidebar
        conversations={state.conversations}
        activeId={state.activeConversationId}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNew={() => dispatch({ type: "NEW_CONVERSATION" })}
        onSelect={(id) => dispatch({ type: "SET_ACTIVE", conversationId: id })}
        onDelete={(id) => dispatch({ type: "DELETE_CONVERSATION", conversationId: id })}
      />

      <div className="flex flex-1 flex-col">
        {showWelcome ? (
          <div className="flex flex-1 flex-col items-center justify-center px-4">
            <div className="mb-8 flex flex-col items-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600">
                <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold tracking-tight">Agentura</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                AI Skills Platform — type a command or pick an action below
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {SUGGESTED_ACTIONS.map((action) => (
                <button
                  key={action.command}
                  onClick={() => handleSuggestedAction(action.command)}
                  className="rounded-xl border border-border bg-card px-4 py-3 text-left text-sm transition-colors hover:border-primary/30 hover:bg-accent/50"
                >
                  <span className="font-medium">{action.label}</span>
                  <p className="mt-0.5 font-mono text-xs text-muted-foreground">{action.command}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <MessageList
            messages={activeConversation?.messages ?? []}
            isThinking={isThinking}
          />
        )}

        <MessageInput
          value={input}
          onChange={setInput}
          onSend={() => sendMessage(input)}
          disabled={isThinking}
        />
      </div>
    </div>
  );
}
