import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearToken, startJob } from "../api";
import StatusCards from "../components/StatusCards";
import OperationGrid from "../components/OperationGrid";
import JobLog from "../components/JobLog";

export default function Dashboard() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobType, setJobType] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const navigate = useNavigate();

  async function handleStart(type: string) {
    try {
      const id = await startJob(type);
      setJobId(id);
      setJobType(type);
      setRunning(true);
    } catch (err) {
      alert((err as Error).message);
    }
  }

  function handleRefresh() {
    setRefreshTrigger(n => n + 1);
  }

  function handleJobDone() {
    setRunning(false);
    setRefreshTrigger(n => n + 1);
  }

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div style={{ background: "#0f172a", minHeight: "100vh", padding: "1.5rem" }}>
      <div style={{ maxWidth: "960px", margin: "0 auto" }}>
        <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#1e293b", padding: "0.75rem 1.25rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          <span style={{ color: "#38bdf8", fontWeight: 700, fontSize: "1rem" }}>Clinicorp ETL</span>
          <button onClick={handleLogout} style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: "0.875rem" }}>
            Sair
          </button>
        </header>

        <StatusCards refreshTrigger={refreshTrigger} />
        <OperationGrid running={running} onStart={handleStart} onRefresh={handleRefresh} />
        <JobLog jobId={jobId} jobType={jobType} onDone={handleJobDone} />
      </div>
    </div>
  );
}
