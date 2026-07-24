import { useEffect, useState } from "react";
import { getStatus } from "../api";

const CARDS = [
  { key: "appointments",  label: "Agendamentos",  color: "#38bdf8" },
  { key: "payments",      label: "Pagamentos",    color: "#34d399" },
  { key: "invoices",      label: "Faturas",       color: "#a78bfa" },
  { key: "patients",      label: "Pacientes",     color: "#fb923c" },
  { key: "professionals", label: "Profissionais", color: "#e2e8f0" },
];

interface Props {
  refreshTrigger: number;
}

export default function StatusCards({ refreshTrigger }: Props) {
  const [data, setData] = useState<Record<string, number | string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getStatus()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [refreshTrigger]);

  const fmt = (v: number | string | undefined) =>
    typeof v === "number" ? v.toLocaleString("pt-BR") : (v ?? "—");

  return (
    <section>
      <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Dashboard</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "0.75rem", marginBottom: "0.75rem" }}>
        {CARDS.map(c => (
          <div key={c.key} style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
            <div style={{ color: c.color, fontSize: "1.5rem", fontWeight: 700 }}>
              {loading ? "..." : fmt(data[c.key])}
            </div>
            <div style={{ color: "#64748b", fontSize: "0.7rem" }}>{c.label}</div>
          </div>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.5rem" }}>
        <div style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
          <div style={{ color: "#fbbf24", fontSize: "0.85rem", fontWeight: 600 }}>
            {String(data.last_sync ?? "—").slice(0, 16).replace("T", " ")}
          </div>
          <div style={{ color: "#64748b", fontSize: "0.7rem" }}>Ultima Sync</div>
        </div>
        <div style={{ background: "#1e293b", borderRadius: "8px", padding: "1rem", textAlign: "center" }}>
          <div style={{ color: loading ? "#64748b" : "#34d399", fontSize: "0.85rem", fontWeight: 600 }}>
            {loading ? "..." : "Conectado"}
          </div>
          <div style={{ color: "#64748b", fontSize: "0.7rem" }}>Status PostgreSQL</div>
        </div>
      </div>
    </section>
  );
}
