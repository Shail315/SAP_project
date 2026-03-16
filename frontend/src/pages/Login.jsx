import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { loginUser } from "../services/api";

function Login() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      const res = await loginUser(form);
      localStorage.setItem("metafuse_token", res.token);
      localStorage.setItem("metafuse_user", JSON.stringify(res.user));
      toast.success("Logged in");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="panel-card w-full max-w-md p-6">
        <h1 className="text-2xl font-bold text-slate-900">Login</h1>
        <p className="mt-1 text-sm text-slate-500">Welcome back to MetaFuse.</p>
        <div className="mt-6 space-y-4">
          <Input
            label="Email"
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <Input
            label="Password"
            type="password"
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <Button className="mt-5 w-full" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </Button>
        <p className="mt-4 text-sm text-slate-500">
          No account? <Link className="font-semibold text-brand-700" to="/signup">Signup</Link>
        </p>
      </form>
    </div>
  );
}

export default Login;
