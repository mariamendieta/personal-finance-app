export default function MetricCard({
  label,
  value,
  accent = "azul",
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  const borderColor = {
    azul: "border-l-azul",
    verde: "border-l-verde-hoja",
    coral: "border-l-coral",
  }[accent] || "border-l-azul";

  return (
    <div className={`bg-cool-white rounded-[10px] px-5 py-4 border-l-4 ${borderColor}`}>
      <p className="text-[0.8rem] font-semibold uppercase tracking-[0.08em] text-stone">
        {label}
      </p>
      <p className="text-2xl font-[Cormorant_Garamond,serif] font-semibold text-warm-charcoal mt-1">
        {value}
      </p>
    </div>
  );
}
