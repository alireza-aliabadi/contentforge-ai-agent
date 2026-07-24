"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ContentJob,
  Platform,
  createJob,
  listJobs,
  listPlatforms,
  uploadDocument,
  uploadImage,
} from "@/lib/api";
import { useAuthStore } from "@/lib/auth";

function scoreLabel(value: number | null | undefined) {
  if (value == null) return "—";
  return `${Math.round(value * 100)}%`;
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token, email, clear } = useAuthStore();
  const [prompt, setPrompt] = useState(
    "Explain retrieval-augmented generation tradeoffs for intermediate engineers.",
  );
  const [platform, setPlatform] = useState<Platform>("linkedin");
  const [assetIds, setAssetIds] = useState<string[]>([]);
  const [selected, setSelected] = useState<ContentJob | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    }
  }, [token, router]);

  const platformsQuery = useQuery({
    queryKey: ["platforms"],
    queryFn: listPlatforms,
    enabled: Boolean(token),
  });

  const jobsQuery = useQuery({
    queryKey: ["jobs", token],
    queryFn: () => listJobs(token!),
    enabled: Boolean(token),
  });

  const createMutation = useMutation({
    mutationFn: () => createJob(token!, { prompt, platform, asset_ids: assetIds }),
    onSuccess: (job) => {
      setSelected(job);
      setMessage("Content package generated.");
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err: Error) => setMessage(err.message),
  });

  const latestPackage = useMemo(() => selected?.packages?.at(-1) ?? null, [selected]);

  async function onUpload(event: FormEvent<HTMLFormElement>, kind: "document" | "image") {
    event.preventDefault();
    if (!token) return;
    const form = event.currentTarget;
    const input = form.elements.namedItem("file") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    try {
      const asset =
        kind === "document" ? await uploadDocument(token, file) : await uploadImage(token, file);
      setAssetIds((prev) => [...prev, asset.id]);
      setMessage(`Attached ${asset.filename}`);
      form.reset();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Upload failed");
    }
  }

  if (!token) {
    return null;
  }

  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-6 py-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link href="/" className="font-[family-name:var(--font-display)] text-2xl font-extrabold text-ink">
            ContentForge
          </Link>
          <p className="text-sm text-ink/60">Signed in as {email}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            clear();
            router.push("/login");
          }}
          className="rounded-md border border-line px-3 py-1.5 text-sm font-medium text-ink hover:border-forge"
        >
          Sign out
        </button>
      </header>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="rounded-2xl border border-ink/10 bg-paper/80 p-5 shadow-sm backdrop-blur">
          <h2 className="font-[family-name:var(--font-display)] text-xl font-bold text-ink">
            Create content
          </h2>
          <p className="mt-1 text-sm text-ink/65">
            Select a platform, attach sources, and run the agent pipeline.
          </p>

          <label className="mt-5 block text-sm font-medium text-ink">
            Platform
            <select
              className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
              value={platform}
              onChange={(e) => setPlatform(e.target.value as Platform)}
            >
              {(platformsQuery.data || []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="mt-4 block text-sm font-medium text-ink">
            Prompt
            <textarea
              className="mt-1 min-h-32 w-full rounded-md border border-line bg-white px-3 py-2"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </label>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <form onSubmit={(e) => onUpload(e, "document")} className="space-y-2">
              <p className="text-sm font-medium text-ink">Documents</p>
              <input name="file" type="file" accept=".pdf,.docx,.txt,.md,.csv" className="block w-full text-sm" />
              <button type="submit" className="rounded-md border border-line px-3 py-1.5 text-xs font-semibold">
                Upload doc
              </button>
            </form>
            <form onSubmit={(e) => onUpload(e, "image")} className="space-y-2">
              <p className="text-sm font-medium text-ink">Images</p>
              <input name="file" type="file" accept=".jpg,.jpeg,.png,.svg" className="block w-full text-sm" />
              <button type="submit" className="rounded-md border border-line px-3 py-1.5 text-xs font-semibold">
                Upload image
              </button>
            </form>
          </div>

          {assetIds.length > 0 && (
            <p className="mt-3 text-xs text-ink/60">{assetIds.length} asset(s) attached</p>
          )}

          <button
            type="button"
            disabled={createMutation.isPending || prompt.trim().length < 10}
            onClick={() => createMutation.mutate()}
            className="mt-5 w-full rounded-md bg-forge px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink disabled:opacity-60"
          >
            {createMutation.isPending ? "Forging content…" : "Generate package"}
          </button>
          {message && <p className="mt-3 text-sm text-ink/70">{message}</p>}
        </section>

        <section className="space-y-4">
          <div className="rounded-2xl border border-ink/10 bg-ink p-5 text-paper">
            <h2 className="font-[family-name:var(--font-display)] text-xl font-bold">Latest package</h2>
            {latestPackage ? (
              <div className="mt-4 space-y-3">
                <h3 className="text-lg font-semibold text-spark">{latestPackage.title}</h3>
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-md bg-white/5 p-3 text-sm leading-relaxed text-paper/90">
                  {latestPackage.body}
                </pre>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded-md bg-white/10 p-2">
                    Originality
                    <div className="mt-1 text-base font-semibold">
                      {scoreLabel(latestPackage.originality_score)}
                    </div>
                  </div>
                  <div className="rounded-md bg-white/10 p-2">
                    Relevance
                    <div className="mt-1 text-base font-semibold">
                      {scoreLabel(latestPackage.relevance_score)}
                    </div>
                  </div>
                  <div className="rounded-md bg-white/10 p-2">
                    Expertise
                    <div className="mt-1 text-base font-semibold">
                      {scoreLabel(latestPackage.expertise_score)}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-paper/70">Generate a job to preview the package here.</p>
            )}
          </div>

          <div className="rounded-2xl border border-ink/10 bg-paper/80 p-5">
            <h2 className="font-[family-name:var(--font-display)] text-xl font-bold text-ink">Recent jobs</h2>
            <ul className="mt-3 space-y-2">
              {(jobsQuery.data || []).map((job) => (
                <li key={job.id}>
                  <button
                    type="button"
                    onClick={() => setSelected(job)}
                    className="w-full rounded-md border border-transparent px-3 py-2 text-left text-sm hover:border-line hover:bg-white"
                  >
                    <span className="font-semibold text-ink">{job.platform}</span>
                    <span className="mx-2 text-ink/40">·</span>
                    <span className="text-ink/70">{job.status}</span>
                    <p className="mt-1 line-clamp-1 text-ink/60">{job.prompt}</p>
                  </button>
                </li>
              ))}
              {!jobsQuery.data?.length && (
                <li className="text-sm text-ink/60">No jobs yet.</li>
              )}
            </ul>
          </div>
        </section>
      </div>
    </main>
  );
}
