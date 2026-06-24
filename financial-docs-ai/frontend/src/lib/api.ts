import { http } from "@/lib/http";

export type ChatThread = {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
};

export type CitationItem = {
  chunkId: string;
  excerpt: string;
  metadata: Record<string, unknown>;
  label?: string;
};

export type ChatUIMessage = {
  id: string;
  role: string;
  parts: Array<{ type: string; text?: string }>;
  citations?: CitationItem[];
};

export const api = {
  listThreads: () => http.get<ChatThread[]>("/chat/threads"),
  createThread: (title = "New chat") => http.post<ChatThread>("/chat/threads", { title }),
  updateThread: (threadId: string, title: string) =>
    http.patch<ChatThread>(`/chat/threads/${threadId}`, { title }),
  listMessages: (threadId: string) => http.get<ChatUIMessage[]>(`/chat/threads/${threadId}/messages`),
};
