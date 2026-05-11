type Props = {
  label: string;
  value: string;
  alert?: boolean;
};

export function KPICard({ label, value, alert }: Props) {
  return (
    <div className="bg-card border border-border p-4 relative">
      <div className="absolute top-0 left-0 text-[8px] text-dim/60 px-1 leading-none">┌</div>
      <div className="absolute top-0 right-0 text-[8px] text-dim/60 px-1 leading-none">┐</div>
      <div className="absolute bottom-0 left-0 text-[8px] text-dim/60 px-1 leading-none">└</div>
      <div className="absolute bottom-0 right-0 text-[8px] text-dim/60 px-1 leading-none">┘</div>
      <div
        className={
          "text-2xl md:text-3xl font-bold tracking-tight tabular-nums " +
          (alert ? "text-alert" : "text-accent")
        }
      >
        {value}
      </div>
      <div className="text-dim text-[10px] uppercase tracking-wider mt-2 leading-snug">
        <span className="text-accent">▸</span> {label}
      </div>
    </div>
  );
}
