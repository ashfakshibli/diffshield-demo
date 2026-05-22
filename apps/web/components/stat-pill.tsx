export function StatPill({ name, value }: { name: string; value: string | number }) {
  return (
    <div className="stat-pill">
      <div className="name">{name}</div>
      <div className="value">{value}</div>
    </div>
  );
}

