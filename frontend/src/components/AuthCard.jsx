import { Link } from "react-router-dom";

export default function AuthCard({
  title,
  subtitle,
  onSubmit,
  loading,
  error,
  footerText,
  footerLinkText,
  footerLinkTo,
  children
}) {
  return (
    <div className="glass-card w-full max-w-md rounded-2xl p-8 shadow-glow">
      <h1 className="font-heading text-3xl font-bold text-brand-700">{title}</h1>
      <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        {children}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-brand-700 px-4 py-3 font-semibold text-white transition hover:bg-brand-800 disabled:opacity-60"
        >
          {loading ? "Please wait..." : title}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-slate-600">
        {footerText}{" "}
        <Link to={footerLinkTo} className="font-semibold text-brand-700 hover:text-brand-900">
          {footerLinkText}
        </Link>
      </p>
    </div>
  );
}
