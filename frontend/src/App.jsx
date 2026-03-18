import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";

const ExternalRedirectComponent = ({ url }) => {
return (
  <div
    style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh"
    }}
  >
    <a href={url} target="_blank" rel="noopener noreferrer">
      Visit Gradio Interface for Demo
    </a>
  </div>
);
};

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/app" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/gradio" element={<ExternalRedirectComponent url="https://fictional-system-97j7p77jq47xf6rp-8002.app.github.dev" />} />
    </Routes>
  );
}
