import type { Message } from './api';

export interface MessageThread {
  conversationId: number;
  messages: Message[];
}

/** A thread from a previous selection must never appear under a new recipient. */
export function messagesForConversation(thread: MessageThread | null, conversationId: number | null): Message[] | null {
  return thread && thread.conversationId === conversationId ? thread.messages : null;
}
