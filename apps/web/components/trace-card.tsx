import type { TraceEvent } from "@/lib/analyzer";

export function TraceCard({ trace }: { trace: TraceEvent }) {
  return (
    <article className="trace-card">
      <div className="trace-meta">
        <span>{trace.stage}</span>
        <span>{new Date(trace.created_at).toLocaleString()}</span>
      </div>
      <h3>{trace.message}</h3>
      <p>{JSON.stringify(trace.payload_json)}</p>
    </article>
  );
}

