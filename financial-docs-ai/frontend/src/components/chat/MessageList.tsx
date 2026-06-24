import type { UIMessage } from "ai";

import { CitationBadge } from "@/components/chat/CitationBadge";
import type { CitationItem } from "@/lib/api";

type MessageWithCitations = UIMessage & { citations?: CitationItem[] };

function messageText(message: MessageWithCitations): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => ("text" in part ? part.text : ""))
    .join("\n");
}

export function MessageList({ messages }: { messages: MessageWithCitations[] }) {
  if (messages.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-[var(--muted)]">
        Ask a question about Apple, Microsoft, NVIDIA, Amazon, or Alphabet filings.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={
            message.role === "user"
              ? "self-end max-w-[85%] rounded-xl bg-[var(--accent)] px-4 py-3 text-white"
              : "self-start max-w-[90%] rounded-xl border border-[var(--border)] bg-[var(--card)] px-4 py-3"
          }
        >
          <p className="whitespace-pre-wrap">{messageText(message)}</p>
          {message.citations && message.citations.length > 0 && (
            <div className="mt-3 flex flex-col gap-2">
              {message.citations.map((citation) => (
                <CitationBadge key={`${message.id}-${citation.chunkId}`} citation={citation} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
