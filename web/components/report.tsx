import { GROUP_ORDER, STATUS_LABEL, type AuditReport, type CheckStatus } from "@/lib/types";

const STATUS_CLASS: Record<CheckStatus, string> = {
  fix: "bg-ink text-on-ink",
  review: "border border-ink-15 text-ink-70",
  clear: "text-ink-55",
};

export function Report({ report }: { report: AuditReport }) {
  const groups = GROUP_ORDER.map((name) => ({
    name,
    checks: report.checks.filter((check) => check.group === name),
  })).filter((group) => group.checks.length > 0);

  const stats = [
    { label: "Title", value: report.page.title_length ? `${report.page.title_length}` : "0", unit: "characters" },
    { label: "Copy", value: `${report.page.word_count}`, unit: "words" },
    {
      label: "Images",
      value: `${report.page.images}`,
      unit: report.page.images === 0 ? "in the HTML" : `${report.page.images_missing_alt} missing alt`,
    },
    {
      label: "Markup",
      value: report.page.schema_types.length ? `${report.page.schema_types.length}` : "0",
      unit: report.page.schema_types.length ? "JSON-LD types" : "JSON-LD types",
    },
  ];

  return (
    <section aria-live="polite" className="mt-16">
      <p className="font-mono text-xs tracking-[0.1em] text-ink-55">01</p>
      <div className="mt-4 grid items-end gap-8 md:grid-cols-[minmax(0,1fr)_auto]">
        <div>
          <h2 className="max-w-xl font-display text-4xl font-light tracking-[-0.025em] text-ink-100 text-balance md:text-5xl">
            {report.summary}
          </h2>
          <p className="mt-4 max-w-xl text-sm leading-relaxed text-ink-55">{report.note}</p>
        </div>
        <p className="font-mono text-6xl font-light leading-none tracking-[-0.04em] text-ink-100 md:text-7xl">
          {report.score}
          <span className="ml-2 align-middle font-sans text-sm tracking-normal text-ink-55">out of 100</span>
        </p>
      </div>
      <div className="mt-8 h-px w-full bg-ink-10" aria-hidden="true">
        <div className="h-px bg-ink" style={{ width: `${report.score}%` }} />
      </div>
      <p className="mt-4 break-all font-mono text-xs text-ink-55">{report.url}</p>
      {report.page.title ? (
        <p className="mt-3 max-w-2xl text-lg font-light leading-snug text-ink-75">{report.page.title}</p>
      ) : null}

      <dl className="mt-10 grid grid-cols-2 gap-3 md:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-ink-07 bg-card px-4 py-5">
            <dt className="text-[11px] uppercase tracking-[0.1em] text-ink-55">{stat.label}</dt>
            <dd className="mt-3 font-mono text-3xl font-light text-ink-100">{stat.value}</dd>
            <dd className="mt-1 text-sm text-ink-55">{stat.unit}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-12 space-y-10">
        {groups.map((group, index) => (
          <section key={group.name}>
            <h3 className="font-mono text-xs tracking-[0.1em] text-ink-55">
              {String(index + 2).padStart(2, "0")} {group.name}
            </h3>
            <ul className="mt-4 divide-y divide-ink-06 rounded-lg border border-ink-07 bg-card">
              {group.checks.map((check) => (
                <li key={check.id} className="grid gap-3 px-5 py-5 sm:grid-cols-[7.5rem_minmax(0,1fr)] sm:gap-6">
                  <p>
                    <span
                      className={`inline-flex min-h-7 items-center rounded-full px-3 text-[11px] uppercase tracking-[0.1em] ${STATUS_CLASS[check.status]}`}
                    >
                      {STATUS_LABEL[check.status]}
                    </span>
                  </p>
                  <div>
                    <p className="text-base text-ink-100">{check.label}</p>
                    <p className="mt-1 text-sm leading-relaxed text-ink-55">{check.detail}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </section>
  );
}
