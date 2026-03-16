import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { signupUser } from "../services/api";

function Signup() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const onSubmit = async (event) => {
    event.preventDefault();
    if (form.password !== form.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const res = await signupUser({
        name: form.name,
        email: form.email,
        password: form.password,
      });
      localStorage.setItem("metafuse_token", res.token);
      localStorage.setItem("metafuse_user", JSON.stringify(res.user));
      toast.success("Account created");
      navigate("/dashboard");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="panel-card w-full max-w-md p-6">
        <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
        <p className="mt-1 text-sm text-slate-500">Start generating metadata with AI.</p>
        <div className="mt-6 space-y-4">
          <Input
            label="Name"
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
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
          <Input
            label="Confirm Password"
            type="password"
            required
            value={form.confirmPassword}
            onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
          />
        </div>
        <Button className="mt-5 w-full" disabled={loading}>
          {loading ? "Creating..." : "Create Account"}
        </Button>
        <p className="mt-4 text-sm text-slate-500">
          Have an account? <Link className="font-semibold text-brand-700" to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}

export default Signup;
