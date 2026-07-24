import { useEffect, useRef, useState } from "react";
import { createLogSocket } from "../api";

const LABEL: Record<string, string> = {
  incremental:   "Sync Incremental",
  full_load:     "Carga Completa",
  patients:      "Sync Pacientes",
  professionals: "Sync Profissionais",
  verify:        "Verificar Integridade",
};

function lineColor(line: string): string {
  if (line.includes("[OK]"))         return "#34d399";
  if (line.includes("[ERROR]") || line.includes("[BATCH ERROR]")) return "#f87171";
  if (line.includes("[FALLBACK]"))   return "#fbbf24";
  if (line.startsWith("==="))        return "#334155";
  return "#94a3b8";
}

interface Props {
  jobId: string | null;
  jobType: string | null;
  onDone: () => void;
}

export default function JobLog({ jobId, jobType, onDone }: Props) {
  const [lines, setLines] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!jobId) return;
    setLines([]);
    setRunning(true);

    const ws = createLogSocket(jobId);

    ws.onmessage = (e) => {
      setLines(prev => [...prev, e.data as string]);
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    ws.onclose = () => {
      setRunning(false);
      onDone();
    };

    return () => ws.close();
  }, [jobId]);

  if (!jobId) return null;

  return (
    <section>
      <p style={{ color: "#64748b", fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "0.5rem" }}>
        Log — {LABEL[jobType ?? ""] ?? jobType}{" "}
        <span style={{ color: running ? "#fbbf24" : "#34d399" }}>
          {running ? "em execucao" : "concluido"}
        </span>
      </p>
      <div style={{ background: "#020617", borderRadius: "8px", padding: "1rem", fontFamily: "monospace", fontSize: "0.78rem", lineHeight: 1.6, height: "240px", overflowY: "auto" }}>
        {lines.map((line, i) => (
          <div key={i} style={{ color: lineColor(line) }}>{line || " "}</div>
        ))}
        {running && <div style={{ color: "#475569" }}>|</div>}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
