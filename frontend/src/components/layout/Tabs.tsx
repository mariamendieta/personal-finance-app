"use client";

import { useState } from "react";

interface TabsProps {
  tabs: string[];
  children: React.ReactNode[];
}

export default function Tabs({ tabs, children }: TabsProps) {
  const [active, setActive] = useState(0);

  return (
    <div>
      <div className="flex gap-0 border-b border-cool-gray mb-6">
        {tabs.map((label, i) => (
          <button
            key={label}
            onClick={() => setActive(i)}
            className={`px-5 py-2 font-[Lora,serif] text-[0.95rem] transition-colors border-b-2 ${
              i === active
                ? "font-semibold text-azul border-azul"
                : "text-stone border-transparent hover:text-azul"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
      {children[active]}
    </div>
  );
}
