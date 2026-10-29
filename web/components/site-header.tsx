import { ThemeToggle } from "@/components/theme-toggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-ink-06 bg-paper/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6 md:px-12">
        <div className="flex items-center gap-4">
          <a
            href="https://jslabs.xyz"
            className="font-display text-[13px] tracking-[0.18em] text-ink-100"
          >
            JS Labs
          </a>
          <span className="text-[13px] tracking-[0.08em] text-ink-55">SEO</span>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
