import { useNavigate } from "react-router-dom";

import Footer from "../components/layout/Footer";
import Navbar from "../components/layout/Navbar";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";

const features = [
  "Title Generator",
  "Description Generator",
  "Tag Generator",
  "Keyword Extractor",
  "Video Summary",
  "Thumbnail Ideas",
];

function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl px-4 py-10 md:px-8">
        <section className="rounded-3xl bg-gradient-to-br from-brand-600 via-indigo-600 to-blue-500 p-8 text-white shadow-soft md:p-12">
          <p className="mb-3 inline-flex rounded-full bg-white/20 px-3 py-1 text-xs font-semibold uppercase tracking-widest">
            AI Metadata Studio
          </p>
          <h1 className="text-4xl font-bold leading-tight md:text-5xl">MetaFuse</h1>
          <p className="mt-2 text-lg text-indigo-100">Generate YouTube Metadata with AI</p>
          <p className="mt-5 max-w-2xl text-indigo-50">
            Upload a video, let AI analyze its content, and get optimized titles,
            descriptions, tags, keywords, summaries, and thumbnail concepts in seconds.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button className="bg-white text-brand-700 hover:bg-indigo-50" onClick={() => navigate("/signup")}>
              Get Started
            </Button>
            <Button variant="secondary" className="border-white/40 bg-white/10 text-white hover:bg-white/20" onClick={() => navigate("/login")}>
              Login
            </Button>
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-2xl font-bold text-slate-900">Features</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <Card key={feature} className="animate-fade-in-up" style={{ animationDelay: `${index * 80}ms` }}>
                <p className="font-semibold text-slate-800">{feature}</p>
                <p className="mt-2 text-sm text-slate-500">Production-grade AI output ready for creators.</p>
              </Card>
            ))}
          </div>
        </section>

        <section className="mt-10 grid gap-4 md:grid-cols-3">
          <Card title="Step 1">
            <p className="text-sm text-slate-600">Upload YouTube video or file</p>
          </Card>
          <Card title="Step 2">
            <p className="text-sm text-slate-600">AI analyzes video</p>
          </Card>
          <Card title="Step 3">
            <p className="text-sm text-slate-600">Generate optimized metadata</p>
          </Card>
        </section>

        <section className="mt-10 grid gap-4 md:grid-cols-3">
          <Card>
            <p className="font-semibold text-slate-800">Save hours of SEO work</p>
          </Card>
          <Card>
            <p className="font-semibold text-slate-800">Improve discoverability</p>
          </Card>
          <Card>
            <p className="font-semibold text-slate-800">AI optimized titles and tags</p>
          </Card>
        </section>
      </main>
      <Footer />
    </div>
  );
}

export default Landing;
