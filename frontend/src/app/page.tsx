import Link from "next/link";

export default function Home() {
  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden px-6 pb-16 pt-8 sm:px-10">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[70vh] bg-[url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2260%22 height=%2260%22 viewBox=%220 0 60 60%22%3E%3Cg fill=%22none%22 stroke=%22%23102820%22 stroke-opacity=%220.05%22%3E%3Cpath d=%22M0 30h60M30 0v60%22/%3E%3C/g%3E%3C/svg%3E')]" />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between">
        <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold tracking-tight text-ink">
          ContentForge
        </p>
        <Link
          href="/login"
          className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-paper transition hover:bg-forge"
        >
          Open studio
        </Link>
      </header>

      <section className="relative z-10 mx-auto mt-16 flex w-full max-w-6xl flex-1 flex-col justify-center gap-10 lg:mt-10 lg:grid lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="animate-rise max-w-2xl">
          <p className="font-[family-name:var(--font-display)] text-5xl font-extrabold leading-[0.95] tracking-tight text-ink sm:text-7xl">
            ContentForge
          </p>
          <div className="forge-line mt-5 h-1 w-40 rounded-full bg-forge" />
          <h1 className="mt-8 max-w-xl text-2xl font-semibold leading-snug text-ink/90 sm:text-3xl">
            Multi-agent content that earns the publish button.
          </h1>
          <p className="animate-rise-delay mt-5 max-w-lg text-base leading-relaxed text-ink/70 sm:text-lg">
            Plan, write, evaluate originality and relevance, then ship platform-ready packages —
            powered by external AI APIs, never local models.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/login"
              className="rounded-md bg-forge px-5 py-3 text-sm font-semibold text-paper shadow-[0_10px_30px_rgba(31,122,92,0.25)] transition hover:-translate-y-0.5 hover:bg-ink"
            >
              Start creating
            </Link>
            <a
              href="#flow"
              className="rounded-md border border-ink/20 bg-paper/60 px-5 py-3 text-sm font-semibold text-ink transition hover:border-forge hover:text-forge"
            >
              See the flow
            </a>
          </div>
        </div>

        <div
          id="flow"
          className="animate-rise-delay relative overflow-hidden rounded-2xl border border-ink/10 bg-ink text-paper"
        >
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-spark/30 blur-2xl" />
          <div className="relative space-y-4 p-6 sm:p-8">
            {[
              "Document & image understanding",
              "Planner → Writer → Evaluators",
              "Optimization loop (≥90% originality & relevance)",
              "Banner generation + final package",
            ].map((step, index) => (
              <div key={step} className="flex items-start gap-4 border-b border-white/10 pb-4 last:border-0 last:pb-0">
                <span className="mt-0.5 font-[family-name:var(--font-display)] text-sm font-bold text-spark">
                  0{index + 1}
                </span>
                <p className="text-sm leading-relaxed text-paper/90 sm:text-base">{step}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
