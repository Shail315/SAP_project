import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import api from "../services/api";

export default function SignupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await api.post("/auth/signup", { name, email, password });
      navigate("/login");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Signup failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-12">
      <AuthCard
        title="Sign Up"
        subtitle="Create your MetaFuse account"
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
        footerText="Already have an account?"
        footerLinkText="Login"
        footerLinkTo="/login"
      >
        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">Name</label>
          <input
            type="text"
            required
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="w-full rounded-xl border border-brand-200 px-4 py-3 outline-none ring-brand-200 transition focus:ring"
            placeholder="Your name"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full rounded-xl border border-brand-200 px-4 py-3 outline-none ring-brand-200 transition focus:ring"
            placeholder="you@example.com"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold text-slate-700">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-xl border border-brand-200 px-4 py-3 outline-none ring-brand-200 transition focus:ring"
            placeholder="At least 8 characters"
          />
        </div>
      </AuthCard>
    </div>
  );
}
