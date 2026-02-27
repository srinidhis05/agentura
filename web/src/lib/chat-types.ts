import type { SkillResult, CorrectResponse, ApprovalResponse } from "./types";
import type { PipelineResult } from "./api";

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
}

export interface ChatState {
  conversations: Conversation[];
  activeConversationId: string | null;
}

export type ChatAction =
  | { type: "NEW_CONVERSATION" }
  | { type: "SET_ACTIVE"; conversationId: string }
  | { type: "DELETE_CONVERSATION"; conversationId: string }
  | { type: "ADD_MESSAGE"; conversationId: string; message: ChatMessage }
  | { type: "LOAD_STATE"; state: ChatState };
