"use client";

import { useReducer, useEffect, useState, useCallback } from "react";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { MessageList } from "@/components/chat/message-list";
import { MessageInput } from "@/components/chat/message-input";
import { AgentPicker } from "@/components/chat/agent-picker";
import type { DomainEntry } from "@/components/chat/agent-picker";
import { ScopedChatHeader } from "@/components/chat/scoped-chat-header";
import { ConversationStarters } from "@/components/chat/conversation-starters";
import { chatReducer, initialState, saveState, loadState } from "@/lib/chat-reducer";
import { routeCommand } from "@/lib/chat-router";
import type { RouteOptions } from "@/lib/chat-router";
import type { ChatMessage, ConversationScope } from "@/lib/chat-types";
import type { PipelineInfo } from "@/lib/api";

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

  const scope = activeConversation?.scope;

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || !state.activeConversationId) return;

      const convId = state.activeConversationId;

      const userMsg: ChatMessage = {
        id: `${Date.now()}-user`,
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };

      dispatch({
        type: "ADD_MESSAGE",
        conversationId: convId,
        message: userMsg,
      });
      setInput("");
      setIsThinking(true);

      // Create a placeholder assistant message for streaming updates
      const placeholderId = `${Date.now()}-assistant`;
      const placeholder: ChatMessage = {
        id: placeholderId,
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };
      dispatch({ type: "ADD_MESSAGE", conversationId: convId, message: placeholder });

      const onUpdate = (content: string) => {
        dispatch({ type: "UPDATE_MESSAGE", conversationId: convId, messageId: placeholderId, content });
      };

      try {
        const opts: RouteOptions = {
          scope: activeConversation?.scope,
          messages: activeConversation?.messages ?? [],
          onUpdate,
        };
        const response = await routeCommand(trimmed, opts);
        // Final update with complete content + metadata
        dispatch({
          type: "UPDATE_MESSAGE",
          conversationId: convId,
          messageId: placeholderId,
          content: response.content,
          metadata: response.metadata,
        });
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        dispatch({
          type: "UPDATE_MESSAGE",
          conversationId: convId,
          messageId: placeholderId,
          content: `Error: ${message}`,
          metadata: { error: message },
        });
      } finally {
        setIsThinking(false);
      }
    },
    [state.activeConversationId, activeConversation?.scope, activeConversation?.messages],
  );

  function handleSelectDomain(domain: DomainEntry) {
    const newScope: ConversationScope = {
      type: "domain",
      id: domain.name,
      displayTitle: domain.name.charAt(0).toUpperCase() + domain.name.slice(1),
      displayAvatar: domain.emoji,
      displayColor: domain.color,
    };
    dispatch({ type: "NEW_SCOPED_CONVERSATION", scope: newScope });
  }

  function handleSelectPipeline(pipeline: PipelineInfo) {
    const newScope: ConversationScope = {
      type: "pipeline",
      id: pipeline.name,
      displayTitle: pipeline.name.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      displayAvatar: pipeline.name.slice(0, 2).toUpperCase(),
      displayColor: "#8b5cf6",
    };
    dispatch({ type: "NEW_SCOPED_CONVERSATION", scope: newScope });
  }

  function handleNewChat() {
    dispatch({ type: "NEW_CONVERSATION" });
  }

  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  const hasMessages = (activeConversation?.messages.length ?? 0) > 0;
  const showPicker = !activeConversation || (!scope && !hasMessages);
  const showStarters = !!scope && !hasMessages;

  const starters: string[] = [];

  const placeholder = scope
    ? `Message ${scope.displayTitle}...`
    : "Message Agentura...";

  return (
    <div className="flex h-screen">
      <ChatSidebar
        conversations={state.conversations}
        activeId={state.activeConversationId}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNew={handleNewChat}
        onSelect={(id) => dispatch({ type: "SET_ACTIVE", conversationId: id })}
        onDelete={(id) => dispatch({ type: "DELETE_CONVERSATION", conversationId: id })}
      />

      <div className="flex flex-1 flex-col">
        {showPicker ? (
          <AgentPicker onSelectDomain={handleSelectDomain} onSelectPipeline={handleSelectPipeline} />
        ) : (
          <>
            {scope && (
              <ScopedChatHeader scope={scope} onNewChat={handleNewChat} />
            )}
            {showStarters ? (
              <div className="flex flex-1 flex-col items-center justify-center">
                <p className="mb-4 text-sm text-muted-foreground">
                  Start a conversation with {scope!.displayTitle}
                </p>
                <ConversationStarters starters={starters} onSelect={sendMessage} />
              </div>
            ) : (
              <MessageList
                messages={activeConversation?.messages ?? []}
                isThinking={isThinking}
              />
            )}
          </>
        )}

        {!showPicker && (
          <MessageInput
            value={input}
            onChange={setInput}
            onSend={() => sendMessage(input)}
            disabled={isThinking}
            placeholder={placeholder}
          />
        )}
      </div>
    </div>
  );
}
