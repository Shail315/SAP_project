import { Link } from "react-router-dom";

const featureCards = [
  {
    title: "Upload to Metadata in Minutes",
    description: "Turn raw videos into title, description, hashtags, and chapters through one intelligent pipeline.",
    image:
      "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80"
  },
  {
    title: "AI-Native Creative Workflow",
    description: "Whisper + semantic ranking + LLM generation gives your content a consistent publishing standard.",
    image:
      "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80"
  },
  {
    title: "Production-Ready Control",
    description: "Regenerate selectively, persist outputs, and review transcript history in a workflow built for teams.",
    image:
      "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1200&q=80"
  }
];

export default function LandingPage() {
  return (
    <main className="px-5 pb-16 pt-8 md:px-10">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between rounded-2xl border border-brand-200 bg-white/75 px-5 py-4 backdrop-blur md:px-8">
        <h1 className="font-heading text-2xl font-bold text-brand-800">MetaFuse</h1>
        <div className="flex items-center gap-3">
          <Link to="/login" className="rounded-xl px-4 py-2 font-semibold text-brand-700 hover:bg-brand-50">
            Login
          </Link>
          <Link to="/signup" className="rounded-xl bg-brand-700 px-4 py-2 font-semibold text-white hover:bg-brand-800">
            Start Free
          </Link>
        </div>
      </header>

      <section className="mx-auto mt-8 grid w-full max-w-6xl items-center gap-8 rounded-3xl border border-brand-100 bg-white p-6 shadow-glow md:grid-cols-2 md:p-10">
        <div>
          <p className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-brand-700">
            AI Video Metadata Platform
          </p>
          <h2 className="mt-4 font-heading text-4xl font-extrabold leading-tight md:text-5xl">
            Publish Faster with <span className="gradient-text">High-Impact Metadata</span>
          </h2>
          <p className="mt-4 max-w-xl text-base text-slate-600 md:text-lg">
            MetaFuse transforms your video transcript into optimized title, description, caption, hashtags, and chapters.
            Built for creators and teams who need quality and speed.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-4">
            <Link to="/signup" className="rounded-xl bg-brand-700 px-6 py-3 font-semibold text-white hover:bg-brand-800">
              Create Account
            </Link>
            <Link to="/login" className="rounded-xl border border-brand-300 px-6 py-3 font-semibold text-brand-700 hover:bg-brand-50">
              Login to Dashboard
            </Link>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl">
          <img
            src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1400&q=80"
            alt="Analytics dashboard"
            className="h-full min-h-[340px] w-full object-cover"
          />
        </div>
      </section>

      <section className="mx-auto mt-10 grid w-full max-w-6xl gap-6 md:grid-cols-3">
        {featureCards.map((feature) => (
          <article key={feature.title} className="overflow-hidden rounded-2xl border border-brand-100 bg-white shadow-sm">
            <img src={feature.image} alt={feature.title} className="h-40 w-full object-cover" />
            <div className="p-5">
              <h3 className="font-heading text-xl font-bold text-brand-800">{feature.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{feature.description}</p>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
