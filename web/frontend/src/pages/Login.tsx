import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, setToken } from "../api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const token = await login(email, password);
      setToken(token);
      navigate("/");
    } catch {
      setError("Email ou senha incorretos");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh" }}>
      <form onSubmit={handleSubmit} style={{ background: "#1e293b", padding: "2rem", borderRadius: "8px", width: "320px", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <h2 style={{ color: "#38bdf8", textAlign: "center", marginBottom: "0.5rem" }}>Clinicorp ETL</h2>
        {error && <p style={{ color: "#f87171", fontSize: "0.875rem" }}>{error}</p>}
        <input
          type="email" placeholder="Email" value={email} required
          onChange={e => setEmail(e.target.value)}
          style={{ padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#e2e8f0" }}
        />
        <input
          type="password" placeholder="Senha" value={password} required
          onChange={e => setPassword(e.target.value)}
          style={{ padding: "0.75rem", background: "#0f172a", border: "1px solid #334155", borderRadius: "4px", color: "#e2e8f0" }}
        />
        <button
          type="submit" disabled={loading}
          style={{ padding: "0.75rem", background: loading ? "#334155" : "#0284c7", color: "white", border: "none", borderRadius: "4px", cursor: loading ? "not-allowed" : "pointer" }}
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
