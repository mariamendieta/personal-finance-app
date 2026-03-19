"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const FLOWER_SVG = `<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" width="40" height="48"><path d="M60 140 C58 120, 52 105, 48 95" stroke="#2D6A4F" stroke-width="0.7" fill="none"/><path d="M28 96 C32 92, 48 88, 68 95 C72 96, 74 97, 72 99 C66 102, 40 102, 28 96Z" fill="#2D6A4F"/><polygon points="42,92 18,42 26,40" fill="#E9A820"/><polygon points="46,90 30,35 38,32" fill="#E9A820"/><polygon points="50,88 40,28 48,26" fill="#E07A5F"/><polygon points="54,87 48,22 56,20" fill="#E07A5F"/><polygon points="58,86 56,16 64,15" fill="#C9184A"/><polygon points="62,87 66,24 72,26" fill="#C9184A"/><path d="M50 92 C48 82, 44 72, 38 58 C36 54, 38 52, 42 54 C50 60, 56 78, 56 92Z" fill="#1B4965"/></svg>`;

const NAV_ITEMS = [
  { href: "/cashflow", label: "Cash Flow" },
  { href: "/investments", label: "Investments" },
  { href: "/action-items", label: "Action Items" },
];

export default function Sidebar({ familyName }: { familyName?: string }) {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-cool-white border-r-[3px] flex flex-col"
      style={{ borderImage: "linear-gradient(180deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1" }}>

      {/* Brand header */}
      <div className="flex items-center gap-3 px-4 py-4 border-b-2 border-azul">
        <div dangerouslySetInnerHTML={{ __html: FLOWER_SVG }} className="shrink-0" />
        <div>
          <h2 className="font-[Cormorant_Garamond,serif] text-[1.15rem] font-medium text-warm-charcoal leading-tight">
            Maria Mendieta
          </h2>
          <p className="text-[0.7rem] font-light text-stone tracking-[0.12em] uppercase mt-0.5">
            Personal Finances
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-6 flex flex-col gap-1 px-2">
        {NAV_ITEMS.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`block px-4 py-2 font-[Lora,serif] text-base transition-colors ${
                active
                  ? "font-semibold text-azul border-b-2 border-azul"
                  : "text-stone hover:text-azul"
              }`}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
