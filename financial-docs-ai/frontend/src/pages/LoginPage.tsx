import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { signIn, signUp } from "@/lib/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSignIn(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    const { error: signInError } = await signIn(email, password);
    setLoading(false);
    if (signInError) {
      setError(signInError.message);
      return;
    }
    navigate("/");
  }

  async function handleSignUp() {
    setLoading(true);
    setError(null);
    const { error: signUpError } = await signUp(email, password);
    setLoading(false);
    if (signUpError) {
      setError(signUpError.message);
      return;
    }
    setError("Account created — check your inbox if email confirmation is enabled.");
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <h1 className="text-xl font-semibold">Document Copilot</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Sign in with your analyst email to query the filing corpus.
        </p>

        <form onSubmit={handleSignIn} className="mt-6 flex flex-col gap-3">
          <Input
            type="email"
            placeholder="you@driftwood.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error && <p className="text-sm text-[var(--danger)]">{error}</p>}

          <div className="flex gap-2">
            <Button type="submit" disabled={loading}>Sign in</Button>
            <Button type="button" variant="ghost" onClick={handleSignUp} disabled={loading}>
              Create account
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
