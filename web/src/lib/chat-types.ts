import type { SkillResult, CorrectResponse, ApprovalResponse } from "./types";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
  metadata?: {
    command?: string;
    skillResult?: SkillResult;
    correctionResult?: CorrectResponse;
    approvalResult?: ApprovalResponse;
    tableData?: { headers: string[]; rows: string[][] };
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
