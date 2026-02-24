import type { ChatState, ChatAction, Conversation } from "./chat-types";

const STORAGE_KEY = "agentura-chat-state";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function createConversation(): Conversation {
  return {
    id: generateId(),
    title: "New Chat",
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

export const initialState: ChatState = {
  conversations: [],
  activeConversationId: null,
};

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case "NEW_CONVERSATION": {
      const conv = createConversation();
      return {
        conversations: [conv, ...state.conversations],
        activeConversationId: conv.id,
      };
    }

    case "SET_ACTIVE":
      return { ...state, activeConversationId: action.conversationId };

    case "DELETE_CONVERSATION": {
      const remaining = state.conversations.filter(
        (c) => c.id !== action.conversationId,
      );
      return {
        conversations: remaining,
        activeConversationId:
          state.activeConversationId === action.conversationId
            ? remaining[0]?.id ?? null
            : state.activeConversationId,
      };
    }

    case "ADD_MESSAGE": {
      return {
        ...state,
        conversations: state.conversations.map((c) => {
          if (c.id !== action.conversationId) return c;
          const messages = [...c.messages, action.message];
          const title =
            c.messages.length === 0 && action.message.role === "user"
              ? action.message.content.slice(0, 40) +
                (action.message.content.length > 40 ? "..." : "")
              : c.title;
          return { ...c, messages, title, updatedAt: Date.now() };
        }),
      };
    }

    case "LOAD_STATE":
      return action.state;

    default:
      return state;
  }
}

export function saveState(state: ChatState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // localStorage full or unavailable
  }
}

export function loadState(): ChatState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ChatState;
  } catch {
    return null;
  }
}
