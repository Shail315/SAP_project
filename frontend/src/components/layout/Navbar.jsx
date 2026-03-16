import { Link, useNavigate } from "react-router-dom";

import Button from "../ui/Button";

function Navbar({ authenticated = false }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("metafuse_token");
    localStorage.removeItem("metafuse_user");
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-white/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-8">
        <Link to="/" className="text-xl font-bold tracking-tight text-slate-900">
          MetaFuse
        </Link>
        <nav className="flex items-center gap-2">
          {!authenticated ? (
            <>
              <Button variant="ghost" onClick={() => navigate("/login")}>Login</Button>
              <Button onClick={() => navigate("/signup")}>Get Started</Button>
            </>
          ) : (
            <Button variant="secondary" onClick={handleLogout}>Logout</Button>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Navbar;
