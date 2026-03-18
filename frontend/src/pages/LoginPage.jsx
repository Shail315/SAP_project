import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AuthCard from "../components/AuthCard";
import api from "../services/api";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", { email, password });
      localStorage.setItem("token", response.data.access_token);
      // const response1 = await api.post("/gradio");
      navigate("/gradio");  
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-12">
      <AuthCard
        title="Login"
        subtitle="Access your MetaFuse workspace"
        onSubmit={handleSubmit}
        loading={loading}
        error={error}
        footerText="Don't have an account?"
        footerLinkText="Sign up"
        footerLinkTo="/signup"
      >
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
            placeholder="••••••••"
          />
        </div>
      </AuthCard>
    </div>
  );
}
