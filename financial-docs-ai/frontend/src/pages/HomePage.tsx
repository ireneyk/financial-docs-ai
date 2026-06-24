import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ChatPanel } from "@/components/chat/ChatPanel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { signOut } from "@/lib/auth";
import { api, type ChatThread, type ChatUIMessage } from "@/lib/api";
import { supabase } from "@/lib/supabase";

export function HomePage() {
  const navigate = useNavigate();
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        navigate("/login");
      }
    });

    api.listThreads()
      .then(setThreads)
      .finally(() => setLoading(false));
  }, [navigate]);

  async function startChat() {
    const thread = await api.createThread();
    navigate(`/chat/${thread.id}`);
  }

  async function handleSignOut() {
    await signOut();
    navigate("/login");
  }

  return (
    <div className="min-h-screen p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Document Copilot</h1>
          <p className="text-sm text-[var(--muted)]">Grounded answers from your SEC filing library.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={startChat}>New chat</Button>
          <Button variant="ghost" onClick={handleSignOut}>Sign out</Button>
        </div>
      </header>

      <Card>
        <h2 className="font-medium">Recent conversations</h2>
        {loading ? (
          <p className="mt-4 text-sm text-[var(--muted)]">Loading threads…</p>
        ) : threads.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--muted)]">No chats yet. Start one to query the corpus.</p>
        ) : (
          <ul className="mt-4 flex flex-col gap-2">
            {threads.map((thread) => (
              <li key={thread.id}>
                <Link
                  to={`/chat/${thread.id}`}
                  className="block rounded-lg border border-[var(--border)] px-3 py-2 hover:bg-[var(--background)]"
                >
                  {thread.title}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export function ChatPage() {
  const { threadId } = useParams();
  const navigate = useNavigate();
  const [initialMessages, setInitialMessages] = useState<ChatUIMessage[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!threadId) {
      navigate("/");
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        navigate("/login");
        return;
      }
      api.listMessages(threadId)
        .then(setInitialMessages)
        .finally(() => setReady(true));
    });
  }, [threadId, navigate]);

  if (!threadId || !ready) {
    return <div className="p-6 text-[var(--muted)]">Loading chat…</div>;
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
        <div className="flex items-center gap-3">
          <Link to="/" className="text-sm text-[var(--muted)] hover:text-[var(--foreground)]">
            ← Back
          </Link>
          <span className="font-medium">Chat</span>
        </div>
      </header>
      <main className="flex-1 min-h-0">
        <ChatPanel threadId={threadId} initialMessages={initialMessages} />
      </main>
    </div>
  );
}
