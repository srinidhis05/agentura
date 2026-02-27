import type { SkillResult, CorrectResponse, ApprovalResponse } from "./types";
import type { PipelineResult } from "./api";

export interface ConversationScope {
  type: "domain" | "pipeline";
  id: string;                // domain name for domains, pipeline name for pipelines
  displayTitle: string;
  displayAvatar: string;     // emoji or 2-char code
  displayColor: string;      // hex color
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  metadata?: {
    command?: string;
    skillResult?: SkillResult;
    pipelineResult?: PipelineResult;
    correctionResult?: CorrectResponse;
    approvalResult?: ApprovalResponse;
    tableData?: { headers: string[]; rows: string[][] };
    routing?: {
      classifier: { domain: string; confidence: number; reasoning: string };
      triage: { route_to: string; reasoning: string };
    };
    error?: string;
  };
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
  scope?: ConversationScope;
}

export interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
}

export type ChatAction =
  | { type: "NEW_CONVERSATION" }
  | { type: "NEW_SCOPED_CONVERSATION"; scope: ConversationScope }
  | { type: "SET_ACTIVE"; conversationId: string }
  | { type: "DELETE_CONVERSATION"; conversationId: string }
  | { type: "ADD_MESSAGE"; conversationId: string; message: ChatMessage }
  | { type: "UPDATE_MESSAGE"; conversationId: string; messageId: string; content: string; metadata?: ChatMessage["metadata"] }
  | { type: "LOAD_STATE"; state: ChatState };
