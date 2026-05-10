type Props = {
  label: string;
  value: string;
  alert?: boolean;
};

export function KPICard({ label, value, alert }: Props) {
  return (
    <div className="bg-card border border-border rounded p-5">
      <div
        className={
          "text-3xl font-semibold tracking-tight " +
          (alert ? "text-alert" : "text-accent")
        }
      >
        {value}
      </div>
      <div className="text-dim text-[10px] uppercase tracking-wider mt-2">
        {label}
      </div>
    </div>
  );
}
