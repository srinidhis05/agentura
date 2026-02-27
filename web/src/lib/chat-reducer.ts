import type { ChatState, ChatAction, Conversation, ConversationScope } from "./chat-types";

const STORAGE_KEY = "agentura-chat-state";

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function createConversation(scope?: ConversationScope): Conversation {
  return {
    id: generateId(),
    title: scope?.displayTitle ?? "New Chat",
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
    scope,
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

    case "NEW_SCOPED_CONVERSATION": {
      const conv = createConversation(action.scope);
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

    case "UPDATE_MESSAGE": {
      return {
        ...state,
        conversations: state.conversations.map((c) => {
          if (c.id !== action.conversationId) return c;
          return {
            ...c,
            updatedAt: Date.now(),
            messages: c.messages.map((m) =>
              m.id === action.messageId
                ? { ...m, content: action.content, ...(action.metadata ? { metadata: action.metadata } : {}) }
                : m,
            ),
          };
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
    const saved = JSON.parse(raw) as ChatState;
    // Drop ghost conversations from pre-picker era (no scope AND no messages)
    saved.conversations = saved.conversations.filter(
      (c: Conversation) => c.scope || c.messages.length > 0,
    );
    if (saved.conversations.length === 0) {
      saved.activeConversationId = null;
    } else if (
      saved.activeConversationId &&
      !saved.conversations.some((c) => c.id === saved.activeConversationId)
    ) {
      saved.activeConversationId = saved.conversations[0]?.id ?? null;
    }
    return saved;
  } catch {
    return null;
  }
}
