"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("admin@contentforge.local");
  const [password, setPassword] = useState("changeme");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (mode === "register") {
        await register(email, password, fullName || undefined);
      }
      const token = await login(email, password);
      setAuth(token.access_token, email);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-6 py-12">
      <Link href="/" className="mb-8 font-[family-name:var(--font-display)] text-2xl font-extrabold text-ink">
        ContentForge
      </Link>
      <h1 className="text-3xl font-semibold tracking-tight text-ink">
        {mode === "login" ? "Welcome back" : "Create your studio"}
      </h1>
      <p className="mt-2 text-sm text-ink/65">
        Default admin: admin@contentforge.local / changeme
      </p>

      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        {mode === "register" && (
          <label className="block text-sm font-medium text-ink">
            Full name
            <input
              className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none ring-forge focus:ring-2"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </label>
        )}
        <label className="block text-sm font-medium text-ink">
          Email
          <input
            type="email"
            required
            className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none ring-forge focus:ring-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="block text-sm font-medium text-ink">
          Password
          <input
            type="password"
            required
            minLength={8}
            className="mt-1 w-full rounded-md border border-line bg-paper px-3 py-2 outline-none ring-forge focus:ring-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-forge px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink disabled:opacity-60"
        >
          {loading ? "Working…" : mode === "login" ? "Sign in" : "Register & sign in"}
        </button>
      </form>

      <button
        type="button"
        className="mt-4 text-sm font-medium text-forge underline-offset-2 hover:underline"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
      >
        {mode === "login" ? "Need an account? Register" : "Already registered? Sign in"}
      </button>
    </main>
  );
}
