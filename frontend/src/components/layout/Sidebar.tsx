"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/cashflow", label: "Cash Flow" },
  { href: "/budget", label: "Budget" },
  { href: "/investments", label: "Investments" },
  { href: "/action-items", label: "Action Items" },
  { href: "/instructions", label: "Instructions" },
];

export default function Sidebar({ familyName }: { familyName?: string }) {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-cool-white border-r-[3px] flex flex-col"
      style={{ borderImage: "linear-gradient(180deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1" }}>

      {/* Brand header */}
      <div className="flex items-center gap-3 px-4 py-4 border-b-2 border-azul">
        <Image src="/logo.png" alt="Bird of Paradise" width={44} height={44} className="shrink-0" />
        <div>
          <h2 className="font-[Cormorant_Garamond,serif] text-[1.1rem] font-medium text-warm-charcoal leading-tight">
            Personal Finance App
          </h2>
          <p className="text-[0.65rem] font-light text-stone tracking-[0.08em] mt-0.5">
            by Maria Mendieta
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
