import { Checker } from "@/components/checker";
import { SiteHeader } from "@/components/site-header";

const READ = [
  {
    index: "01",
    title: "Fix",
    body: "The page is missing something this check treats as required, such as a title, a heading, or an indexable response.",
  },
  {
    index: "02",
    title: "Review",
    body: "The item is present, but it is short, long, or incomplete. A short homepage can land here on purpose.",
  },
  {
    index: "03",
    title: "Clear",
    body: "This item passed. The score is the share of checks that are clear, with a review counting as part of a pass.",
  },
];

const LOOKS = [
  { index: "01", title: "Index", body: "Response, HTTPS, title, description, indexing, canonical, language and viewport." },
  { index: "02", title: "Copy", body: "The H1, visible length, a quality heuristic, and whether the snippet repeats the title." },
  { index: "03", title: "Rest of the page", body: "Image alt text, links on the same host, JSON-LD, and the Open Graph preview." },
];

export default function Page() {
  return (
    <>
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-30 focus:bg-card focus:px-4 focus:py-3"
      >
        Skip to content
      </a>
      <SiteHeader />
      <main id="content">
        <section className="mx-auto max-w-6xl px-6 pb-24 pt-16 md:px-12 md:pt-24">
          <p className="text-[12px] uppercase tracking-[0.1em] text-ink-55">Page check</p>
          <h1 className="mt-4 max-w-3xl font-display text-5xl font-light leading-[1.05] tracking-[-0.025em] text-ink-100 text-balance sm:text-6xl">
            See what one page is missing.
          </h1>
          <p className="mt-6 max-w-2xl text-2xl font-light leading-snug text-ink-60">
            Paste a public address. The check reads the HTML the server sends back and lists what to fix first.
          </p>
          <Checker />
        </section>

        <section className="border-t border-ink-06">
          <div className="mx-auto max-w-6xl px-6 py-24 md:px-12 md:py-32">
            <p className="text-[12px] uppercase tracking-[0.1em] text-ink-55">How to read it</p>
            <h2 className="mt-4 max-w-2xl font-display text-4xl font-light tracking-[-0.025em] text-ink-100 md:text-5xl">
              Fix, review, or clear.
            </h2>
            <div className="mt-16 grid gap-3 md:grid-cols-3">
              {READ.map((item) => (
                <article key={item.index} className="rounded-lg border border-ink-07 bg-card p-6">
                  <p className="font-mono text-xs text-ink-55">{item.index}</p>
                  <h3 className="mt-6 text-2xl font-light tracking-[-0.025em] text-ink-100">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-ink-55">{item.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-ink-06 bg-paper-edge">
          <div className="mx-auto max-w-6xl px-6 py-24 md:px-12 md:py-32">
            <p className="text-[12px] uppercase tracking-[0.1em] text-ink-55">What it looks at</p>
            <h2 className="mt-4 max-w-2xl font-display text-4xl font-light tracking-[-0.025em] text-ink-100 md:text-5xl">
              One page of server HTML.
            </h2>
            <div className="mt-16 grid gap-3 md:grid-cols-3">
              {LOOKS.map((item) => (
                <article key={item.index} className="rounded-lg border border-ink-07 bg-card p-6">
                  <p className="font-mono text-xs text-ink-55">{item.index}</p>
                  <h3 className="mt-6 text-lg font-light text-ink-100">{item.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-ink-55">{item.body}</p>
                </article>
              ))}
            </div>
            <p className="mt-10 max-w-2xl text-sm leading-relaxed text-ink-55">
              Pages built only in the browser can look thinner here than they do on screen. The parsers come from
              Claude SEO, an MIT project. Nothing you submit is stored.
            </p>
          </div>
        </section>

        <section className="border-t border-ink-06">
          <div className="mx-auto max-w-xl px-6 py-24 text-center md:py-32">
            <h2 className="font-display text-4xl font-light tracking-[-0.025em] text-ink-100 md:text-5xl">
              Send the job you want gone.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-55">
              Tell me the page, the channel, and what is stuck.
            </p>
            <a
              href="https://jslabs.xyz/contact"
              className="press-feedback mt-8 inline-flex min-h-11 items-center justify-center rounded-xl bg-ink px-8 text-sm font-medium tracking-[0.1em] text-on-ink hover:bg-ink-soft"
            >
              Start a conversation
            </a>
          </div>
        </section>
      </main>
      <footer className="border-t border-ink-06">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-6 py-8 text-[12px] uppercase tracking-[0.1em] text-ink-55 md:flex-row md:items-center md:justify-between md:px-12">
          <a href="https://jslabs.xyz" className="hover:text-ink-100">
            JS Labs
          </a>
          <a href="https://github.com/AgriciDaniel/claude-seo" className="hover:text-ink-100">
            Claude SEO, MIT
          </a>
        </div>
      </footer>
    </>
  );
}
