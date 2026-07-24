const OPS = [
  { type: "incremental",   label: "Sync Incremental",     desc: "Dados do dia",         icon: ">>", primary: true },
  { type: "full_load",     label: "Carga Completa",       desc: "Desde 2020",           icon: "[]", primary: false },
  { type: "patients",      label: "Sync Pacientes",       desc: "Novos cadastros",      icon: "P",  primary: false },
  { type: "professionals", label: "Sync Profissionais",   desc: "Equipe clinica",       icon: "+",  primary: false },
  { type: "verify",        label: "Verificar Integridade", desc: "Diagnostico FK",      icon: "?",  primary: false },
  { type: "__refresh__",   label: "Atualizar Status",     desc: "Recarregar contagens", icon: "R",  primary: false },
] as const;

interface Props {
  running: boolean;
  onStart: (type: string) => void;
  onRefresh: () => void;
}

export default function OperationGrid({ running, onStart, onRefresh }: Props) {
  return (
    <section>
      <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>Operacoes</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem", marginBottom: "1.5rem" }}>
        {OPS.map(op => {
          const disabled = running && op.type !== "__refresh__";
          return (
            <button
              key={op.type}
              disabled={disabled}
              onClick={() => op.type === "__refresh__" ? onRefresh() : onStart(op.type)}
              style={{
                background: disabled ? "#1a2332" : op.primary ? "#0284c7" : "#1e293b",
                border: `1px solid ${disabled ? "#1e2d3f" : op.primary ? "#0284c7" : "#334155"}`,
                color: disabled ? "#334155" : "#e2e8f0",
                borderRadius: "8px",
                padding: "0.875rem",
                cursor: disabled ? "not-allowed" : "pointer",
                textAlign: "center",
                transition: "background 0.15s",
              }}
            >
              <div style={{ fontSize: "1.25rem", marginBottom: "0.25rem" }}>{op.icon}</div>
              <div style={{ fontWeight: 600, fontSize: "0.8rem" }}>{op.label}</div>
              <div style={{ fontSize: "0.72rem", color: disabled ? "#334155" : "#64748b" }}>{op.desc}</div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
