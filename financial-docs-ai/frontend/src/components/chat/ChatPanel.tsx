import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useMemo, useState } from "react";

import { MessageList } from "@/components/chat/MessageList";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getAccessToken } from "@/lib/auth";
import { api, type ChatUIMessage, type CitationItem } from "@/lib/api";
import { env } from "@/lib/env";

type ChatPanelProps = {
  threadId: string;
  initialMessages: ChatUIMessage[];
};

export function ChatPanel({ threadId, initialMessages }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [storedMessages, setStoredMessages] = useState<ChatUIMessage[]>(initialMessages);

  useEffect(() => {
    setStoredMessages(initialMessages);
  }, [initialMessages]);

  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${env.apiBaseUrl}/chat/stream`,
        headers: async () => {
          const token = await getAccessToken();
          return token ? { Authorization: `Bearer ${token}` } : {};
        },
        body: { threadId },
      }),
    [threadId],
  );

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages as never,
    transport,
  });

  useEffect(() => {
    if (status !== "streaming") {
      api.listMessages(threadId).then(setStoredMessages).catch(() => undefined);
    }
  }, [threadId, status]);

  const enrichedMessages = messages.map((message) => {
    const stored = storedMessages.find((item) => item.id === message.id);
    return {
      ...message,
      citations: (stored?.citations ?? (message as { citations?: CitationItem[] }).citations) as
        | CitationItem[]
        | undefined,
    };
  });

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || status === "streaming") {
      return;
    }
    setInput("");
    await sendMessage({ text });
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ScrollArea className="flex-1 min-h-0">
        <MessageList messages={enrichedMessages} />
      </ScrollArea>

      {error && (
        <p className="px-4 py-2 text-sm text-[var(--danger)]">
          {error.message || "Something went wrong while streaming the answer."}
        </p>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-[var(--border)] p-4">
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about revenue mix, risk factors, capex…"
          disabled={status === "streaming"}
        />
        <Button type="submit" disabled={status === "streaming" || input.trim() === ""}>
          {status === "streaming" ? "Thinking…" : "Send"}
        </Button>
      </form>
    </div>
  );
}
